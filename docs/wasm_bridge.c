/**
 * FoxVC WebAssembly Bridge (wasm_bridge.c)
 * Standalone client-side compiler and bytecode VM runner for FoxVC in WebAssembly.
 *
 * Compiles FoxVC source code into bytecode and executes it via the compact FoxVM
 * engine, capturing stdout into a safe memory buffer for JavaScript consumption.
 *
 * Emscripten Compilation:
 *   emcc wasm_bridge.c -O3 -s WASM=1 \
 *        -s EXPORTED_FUNCTIONS="['_run_foxvc', '_malloc', '_free']" \
 *        -s EXPORTED_RUNTIME_METHODS="['cwrap', 'stringToUTF8', 'UTF8ToString']" \
 *        -s ALLOW_MEMORY_GROWTH=1 \
 *        -o foxvm.js
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <math.h>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#define EMSCRIPTEN_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define EMSCRIPTEN_EXPORT
#endif

/* ============================================================================
 * Output Capture Buffer
 * ============================================================================ */
#define MAX_OUT_BUF (512 * 1024)
static char g_out_buf[MAX_OUT_BUF];
static int g_out_pos = 0;

static void out_reset(void) {
    g_out_pos = 0;
    g_out_buf[0] = '\0';
}

static void out_puts(const char* text) {
    int len = (int)strlen(text);
    if (g_out_pos + len + 2 < MAX_OUT_BUF) {
        memcpy(g_out_buf + g_out_pos, text, len);
        g_out_pos += len;
        g_out_buf[g_out_pos++] = '\n';
        g_out_buf[g_out_pos] = '\0';
    }
}

static void out_printf(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    char tmp[1024];
    vsnprintf(tmp, sizeof(tmp), fmt, args);
    va_end(args);
    out_puts(tmp);
}

/* ============================================================================
 * FoxVM Compact Virtual Machine Runtime
 * ============================================================================ */
#define MAX_REGS 256
#define MAX_VARS 512
#define MAX_CALL_STACK 1024
#define MAX_PACKS 4096
#define ARENA_SIZE_BYTES (8 * 1024 * 1024)

typedef struct {
    double* data;
    int capacity;
    int size;
} FoxPack;

typedef struct {
    int return_ip;
    int target_reg;
    double saved_regs[MAX_REGS];
} FoxFrame;

static FoxPack heap_packs[MAX_PACKS];
static int pack_count = 0;
static char g_memory_arena[ARENA_SIZE_BYTES];
static size_t g_arena_offset = 0;

static void reset_memory_arena(void) {
    g_arena_offset = 0;
    pack_count = 0;
}

static void* arena_alloc(size_t size) {
    size_t aligned = (size + 7) & ~((size_t)7);
    if (g_arena_offset + aligned > ARENA_SIZE_BYTES) return NULL;
    void* ptr = (void*)&g_memory_arena[g_arena_offset];
    g_arena_offset += aligned;
    return ptr;
}

static int allocate_pack(int initial_cap) {
    if (pack_count >= MAX_PACKS) return -1;
    int cap = initial_cap > 0 ? initial_cap : 16;
    double* data = (double*)arena_alloc(cap * sizeof(double));
    if (!data) return -1;
    int id = pack_count++;
    heap_packs[id].capacity = cap;
    heap_packs[id].size = 0;
    heap_packs[id].data = data;
    memset(heap_packs[id].data, 0, cap * sizeof(double));
    return id;
}

static double run_bytecode(int* inst, int inst_len, double* num_consts, int num_consts_len, const char** str_consts, int str_consts_len) {
    reset_memory_arena();
    double regs[MAX_REGS] = {0.0};
    double vars[MAX_VARS] = {0.0};
    FoxFrame call_stack[MAX_CALL_STACK];
    int call_sp = 0;
    int ip = 0;
    int step_limit = 2000000; // Protection against infinite loops in WASM
    int steps = 0;

    while (ip < inst_len) {
        if (++steps > step_limit) {
            out_puts("Error: Execution step limit reached (potential infinite loop terminated).");
            return -1.0;
        }

        int op = inst[ip++];
        switch (op) {
            case 1: { // LOAD_CONST
                int r = inst[ip++]; int c = inst[ip++];
                regs[r] = (c >= 0 && c < num_consts_len) ? num_consts[c] : 0.0;
                break;
            }
            case 2: { // LOAD_VAR
                int d = inst[ip++]; int v = inst[ip++];
                regs[d] = (v >= 0 && v < MAX_VARS) ? vars[v] : 0.0;
                break;
            }
            case 3: { // STORE_VAR
                int v = inst[ip++]; int s = inst[ip++];
                if (v >= 0 && v < MAX_VARS) vars[v] = regs[s];
                break;
            }
            case 4: { // ADD
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = regs[a] + regs[b];
                break;
            }
            case 5: { // SUB
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = regs[a] - regs[b];
                break;
            }
            case 6: { // MUL
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = regs[a] * regs[b];
                break;
            }
            case 7: { // DIV
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[b] != 0.0) ? (regs[a] / regs[b]) : 0.0;
                break;
            }
            case 8: { // MOD
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[b] != 0.0) ? fmod(regs[a], regs[b]) : 0.0;
                break;
            }
            case 9: { // CMP_EQ
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] == regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 10: { // CMP_NE
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] != regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 11: { // CMP_LT
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] < regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 12: { // CMP_GT
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] > regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 13: { // CMP_LE
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] <= regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 14: { // CMP_GE
                int d = inst[ip++]; int a = inst[ip++]; int b = inst[ip++];
                regs[d] = (regs[a] >= regs[b]) ? 1.0 : 0.0;
                break;
            }
            case 15: { // JUMP
                ip = inst[ip];
                break;
            }
            case 16: { // JUMP_IF_FALSE
                int cond = inst[ip++];
                int target = inst[ip++];
                if (regs[cond] == 0.0) ip = target;
                break;
            }
            case 17: { // HALT
                return regs[0];
            }
            case 19: { // CALL
                int f_addr = inst[ip++];
                int argc = inst[ip++];
                int res_reg = inst[ip++];
                if (call_sp >= MAX_CALL_STACK) {
                    out_puts("Error: Call stack overflow.");
                    return -1.0;
                }
                for (int i = 0; i < MAX_REGS; i++) call_stack[call_sp].saved_regs[i] = regs[i];
                call_stack[call_sp].return_ip = ip + argc;
                call_stack[call_sp].target_reg = res_reg;
                call_sp++;
                double temp[MAX_REGS];
                for (int i = 0; i < argc; i++) temp[i] = regs[inst[ip + i]];
                for (int i = 0; i < argc; i++) regs[i] = temp[i];
                ip = f_addr;
                break;
            }
            case 20: { // RETURN
                int v_reg = inst[ip++];
                double val = regs[v_reg];
                if (call_sp <= 0) return val;
                call_sp--;
                int ret_ip = call_stack[call_sp].return_ip;
                int tgt_reg = call_stack[call_sp].target_reg;
                for (int i = 0; i < MAX_REGS; i++) regs[i] = call_stack[call_sp].saved_regs[i];
                regs[tgt_reg] = val;
                ip = ret_ip;
                break;
            }
            case 21: { // PRINT (Captures to WASM buffer)
                int is_str = inst[ip++];
                int idx = inst[ip++];
                if (is_str) {
                    if (str_consts && idx >= 0 && idx < str_consts_len) {
                        out_puts(str_consts[idx]);
                    }
                } else {
                    double val = regs[idx];
                    char num_buf[64];
                    if (val == (long long)val) {
                        snprintf(num_buf, sizeof(num_buf), "%lld", (long long)val);
                    } else {
                        snprintf(num_buf, sizeof(num_buf), "%g", val);
                    }
                    out_puts(num_buf);
                }
                break;
            }
            case 22: { // EMIT
                int s = inst[ip++];
                return regs[s];
            }
            case 24: { // SIN
                int d = inst[ip++]; int s = inst[ip++];
                regs[d] = sin(regs[s]);
                break;
            }
            case 25: { // COS
                int d = inst[ip++]; int s = inst[ip++];
                regs[d] = cos(regs[s]);
                break;
            }
            case 26: { // SQRT
                int d = inst[ip++]; int s = inst[ip++];
                regs[d] = (regs[s] >= 0.0) ? sqrt(regs[s]) : 0.0;
                break;
            }
            case 28: { // BUILD_LIST
                int cap_idx = inst[ip++]; int dst = inst[ip++]; int count = inst[ip++];
                int cap = count > 0 ? count : 16;
                int pid = allocate_pack(cap);
                regs[dst] = (double)pid;
                if (pid >= 0 && pid < pack_count) {
                    heap_packs[pid].size = count;
                    for (int i = 0; i < count; i++) {
                        int r = inst[ip++];
                        if (i < heap_packs[pid].capacity) heap_packs[pid].data[i] = regs[r];
                    }
                } else {
                    ip += count;
                }
                break;
            }
            case 29: { // GET_INDEX
                int dst = inst[ip++]; int pid_reg = inst[ip++]; int idx_reg = inst[ip++];
                int pid = (int)regs[pid_reg]; int idx = (int)regs[idx_reg];
                if (pid >= 0 && pid < pack_count && idx >= 0 && idx < heap_packs[pid].capacity) {
                    regs[dst] = heap_packs[pid].data[idx];
                } else {
                    regs[dst] = 0.0;
                }
                break;
            }
            case 30: { // SET_INDEX
                int pid_reg = inst[ip++]; int idx_reg = inst[ip++]; int val_reg = inst[ip++];
                int pid = (int)regs[pid_reg]; int idx = (int)regs[idx_reg];
                if (pid >= 0 && pid < pack_count && idx >= 0 && idx < heap_packs[pid].capacity) {
                    heap_packs[pid].data[idx] = regs[val_reg];
                }
                break;
            }
            default:
                break;
        }
    }
    return regs[0];
}

/* ============================================================================
 * Lightweight Parser & Bytecode Compiler for WebAssembly Bridge
 * ============================================================================ */
#define MAX_BYTECODE 8192
#define MAX_CONSTS 512

typedef struct {
    int inst[MAX_BYTECODE];
    int inst_len;
    double num_consts[MAX_CONSTS];
    int num_consts_len;
    char str_consts[MAX_CONSTS][256];
    int str_consts_len;
    char var_names[MAX_VARS][64];
    int var_count;
    char func_names[64][64];
    int func_addrs[64];
    int func_count;
    int next_reg;
} CompilerContext;

static int add_num_const(CompilerContext* ctx, double val) {
    for (int i = 0; i < ctx->num_consts_len; i++) {
        if (ctx->num_consts[i] == val) return i;
    }
    if (ctx->num_consts_len < MAX_CONSTS) {
        ctx->num_consts[ctx->num_consts_len] = val;
        return ctx->num_consts_len++;
    }
    return 0;
}

static int add_str_const(CompilerContext* ctx, const char* str) {
    for (int i = 0; i < ctx->str_consts_len; i++) {
        if (strcmp(ctx->str_consts[i], str) == 0) return i;
    }
    if (ctx->str_consts_len < MAX_CONSTS) {
        strncpy(ctx->str_consts[ctx->str_consts_len], str, 255);
        ctx->str_consts[ctx->str_consts_len][255] = '\0';
        return ctx->str_consts_len++;
    }
    return 0;
}

static int g_var_str_idx[MAX_VARS];
static int g_reg_str_idx[MAX_REGS];

static void init_str_tracking(void) {
    for (int i = 0; i < MAX_VARS; i++) g_var_str_idx[i] = -1;
    for (int i = 0; i < MAX_REGS; i++) g_reg_str_idx[i] = -1;
}

static int get_var_index(CompilerContext* ctx, const char* name) {
    for (int i = 0; i < ctx->var_count; i++) {
        if (strcmp(ctx->var_names[i], name) == 0) return i;
    }
    if (ctx->var_count < MAX_VARS) {
        strncpy(ctx->var_names[ctx->var_count], name, 63);
        ctx->var_names[ctx->var_count][63] = '\0';
        return ctx->var_count++;
    }
    return 0;
}

/* Tokenizer */
typedef enum {
    TOK_EOF, TOK_NEWLINE, TOK_NUMBER, TOK_STRING, TOK_IDENT,
    TOK_KW_LOCK, TOK_KW_SHIFT, TOK_KW_ACT, TOK_KW_EMIT, TOK_KW_SAY,
    TOK_KW_PICK, TOK_KW_ALT, TOK_KW_OTHERWISE, TOK_KW_SPIN, TOK_KW_CYCLE,
    TOK_KW_HALT, TOK_KW_SKIP, TOK_KW_AYE, TOK_KW_NAY, TOK_KW_ALSO,
    TOK_KW_EITHER, TOK_KW_DENY, TOK_KW_PACK, TOK_KW_GUARD, TOK_KW_TRAP,
    TOK_EQUAL, TOK_PLUS, TOK_MINUS, TOK_STAR, TOK_SLASH, TOK_PERCENT,
    TOK_EQEQ, TOK_NOTEQ, TOK_LT, TOK_LTEQ, TOK_GT, TOK_GTEQ,
    TOK_LPAREN, TOK_RPAREN, TOK_COMMA, TOK_COLON
} TokenType;

typedef struct {
    TokenType type;
    double num_val;
    char text[256];
    int line;
} Token;

typedef struct {
    const char* src;
    int pos;
    int line;
    Token cur;
} Lexer;

static void lex_advance(Lexer* lex) {
    while (lex->src[lex->pos]) {
        char c = lex->src[lex->pos];
        if (c == ' ' || c == '\t' || c == '\r') {
            lex->pos++;
            continue;
        }
        if (c == '#') { // Comment
            while (lex->src[lex->pos] && lex->src[lex->pos] != '\n') lex->pos++;
            continue;
        }
        if (c == '\n') {
            lex->line++;
            lex->pos++;
            lex->cur.type = TOK_NEWLINE;
            lex->cur.line = lex->line;
            return;
        }
        break;
    }

    if (!lex->src[lex->pos]) {
        lex->cur.type = TOK_EOF;
        return;
    }

    char c = lex->src[lex->pos];
    lex->cur.line = lex->line;

    if (isdigit((unsigned char)c)) {
        char* end;
        lex->cur.num_val = strtod(&lex->src[lex->pos], &end);
        lex->pos = (int)(end - lex->src);
        lex->cur.type = TOK_NUMBER;
        return;
    }

    if (c == '"' || c == '\'') {
        char quote = c;
        lex->pos++;
        int p = 0;
        while (lex->src[lex->pos] && lex->src[lex->pos] != quote && p < 255) {
            if (lex->src[lex->pos] == '\\' && lex->src[lex->pos + 1]) {
                lex->pos++;
                char esc = lex->src[lex->pos++];
                if (esc == 'n') lex->cur.text[p++] = '\n';
                else if (esc == 't') lex->cur.text[p++] = '\t';
                else lex->cur.text[p++] = esc;
            } else {
                lex->cur.text[p++] = lex->src[lex->pos++];
            }
        }
        if (lex->src[lex->pos] == quote) lex->pos++;
        lex->cur.text[p] = '\0';
        lex->cur.type = TOK_STRING;
        return;
    }

    if (isalpha((unsigned char)c) || c == '_') {
        int p = 0;
        while ((isalnum((unsigned char)lex->src[lex->pos]) || lex->src[lex->pos] == '_') && p < 255) {
            lex->cur.text[p++] = lex->src[lex->pos++];
        }
        lex->cur.text[p] = '\0';

        if (strcmp(lex->cur.text, "lock") == 0) lex->cur.type = TOK_KW_LOCK;
        else if (strcmp(lex->cur.text, "shift") == 0) lex->cur.type = TOK_KW_SHIFT;
        else if (strcmp(lex->cur.text, "act") == 0) lex->cur.type = TOK_KW_ACT;
        else if (strcmp(lex->cur.text, "emit") == 0) lex->cur.type = TOK_KW_EMIT;
        else if (strcmp(lex->cur.text, "say") == 0) lex->cur.type = TOK_KW_SAY;
        else if (strcmp(lex->cur.text, "pick") == 0) lex->cur.type = TOK_KW_PICK;
        else if (strcmp(lex->cur.text, "alt") == 0) lex->cur.type = TOK_KW_ALT;
        else if (strcmp(lex->cur.text, "otherwise") == 0) lex->cur.type = TOK_KW_OTHERWISE;
        else if (strcmp(lex->cur.text, "spin") == 0) lex->cur.type = TOK_KW_SPIN;
        else if (strcmp(lex->cur.text, "cycle") == 0) lex->cur.type = TOK_KW_CYCLE;
        else if (strcmp(lex->cur.text, "halt") == 0) lex->cur.type = TOK_KW_HALT;
        else if (strcmp(lex->cur.text, "skip") == 0) lex->cur.type = TOK_KW_SKIP;
        else if (strcmp(lex->cur.text, "aye") == 0) lex->cur.type = TOK_KW_AYE;
        else if (strcmp(lex->cur.text, "nay") == 0) lex->cur.type = TOK_KW_NAY;
        else if (strcmp(lex->cur.text, "also") == 0) lex->cur.type = TOK_KW_ALSO;
        else if (strcmp(lex->cur.text, "either") == 0) lex->cur.type = TOK_KW_EITHER;
        else if (strcmp(lex->cur.text, "deny") == 0) lex->cur.type = TOK_KW_DENY;
        else if (strcmp(lex->cur.text, "pack") == 0) lex->cur.type = TOK_KW_PACK;
        else if (strcmp(lex->cur.text, "guard") == 0) lex->cur.type = TOK_KW_GUARD;
        else if (strcmp(lex->cur.text, "trap") == 0) lex->cur.type = TOK_KW_TRAP;
        else lex->cur.type = TOK_IDENT;
        return;
    }

    lex->pos++;
    if (c == '=') {
        if (lex->src[lex->pos] == '=') { lex->pos++; lex->cur.type = TOK_EQEQ; }
        else { lex->cur.type = TOK_EQUAL; }
    } else if (c == '!') {
        if (lex->src[lex->pos] == '=') { lex->pos++; lex->cur.type = TOK_NOTEQ; }
    } else if (c == '<') {
        if (lex->src[lex->pos] == '=') { lex->pos++; lex->cur.type = TOK_LTEQ; }
        else { lex->cur.type = TOK_LT; }
    } else if (c == '>') {
        if (lex->src[lex->pos] == '=') { lex->pos++; lex->cur.type = TOK_GTEQ; }
        else { lex->cur.type = TOK_GT; }
    } else if (c == '+') lex->cur.type = TOK_PLUS;
    else if (c == '-') lex->cur.type = TOK_MINUS;
    else if (c == '*') lex->cur.type = TOK_STAR;
    else if (c == '/') lex->cur.type = TOK_SLASH;
    else if (c == '%') lex->cur.type = TOK_PERCENT;
    else if (c == '(') lex->cur.type = TOK_LPAREN;
    else if (c == ')') lex->cur.type = TOK_RPAREN;
    else if (c == ',') lex->cur.type = TOK_COMMA;
    else if (c == ':') lex->cur.type = TOK_COLON;
    else { lex->cur.type = TOK_IDENT; lex->cur.text[0] = c; lex->cur.text[1] = '\0'; }
}

/* Recursive Descent Expression Parser */
static int parse_expression(Lexer* lex, CompilerContext* ctx);

static int parse_primary(Lexer* lex, CompilerContext* ctx) {
    int r = ctx->next_reg++;
    if (lex->cur.type == TOK_NUMBER) {
        int c = add_num_const(ctx, lex->cur.num_val);
        ctx->inst[ctx->inst_len++] = 1; // LOAD_CONST
        ctx->inst[ctx->inst_len++] = r;
        ctx->inst[ctx->inst_len++] = c;
        lex_advance(lex);
        return r;
    }
    if (lex->cur.type == TOK_STRING) {
        int s = add_str_const(ctx, lex->cur.text);
        int c = add_num_const(ctx, 0.0);
        ctx->inst[ctx->inst_len++] = 1; // LOAD_CONST
        ctx->inst[ctx->inst_len++] = r;
        ctx->inst[ctx->inst_len++] = c;
        if (r < MAX_REGS) g_reg_str_idx[r] = s;
        lex_advance(lex);
        return r;
    }
    if (lex->cur.type == TOK_KW_AYE) {
        int c = add_num_const(ctx, 1.0);
        ctx->inst[ctx->inst_len++] = 1;
        ctx->inst[ctx->inst_len++] = r;
        ctx->inst[ctx->inst_len++] = c;
        lex_advance(lex);
        return r;
    }
    if (lex->cur.type == TOK_KW_NAY) {
        int c = add_num_const(ctx, 0.0);
        ctx->inst[ctx->inst_len++] = 1;
        ctx->inst[ctx->inst_len++] = r;
        ctx->inst[ctx->inst_len++] = c;
        lex_advance(lex);
        return r;
    }
    if (lex->cur.type == TOK_IDENT) {
        char name[64];
        strncpy(name, lex->cur.text, 63);
        name[63] = '\0';
        lex_advance(lex);

        if (lex->cur.type == TOK_LPAREN) { // Function Call
            lex_advance(lex);
            int arg_regs[16];
            int argc = 0;
            while (lex->cur.type != TOK_RPAREN && lex->cur.type != TOK_EOF && argc < 16) {
                arg_regs[argc++] = parse_expression(lex, ctx);
                if (lex->cur.type == TOK_COMMA) lex_advance(lex);
            }
            if (lex->cur.type == TOK_RPAREN) lex_advance(lex);

            int f_addr = -1;
            for (int i = 0; i < ctx->func_count; i++) {
                if (strcmp(ctx->func_names[i], name) == 0) {
                    f_addr = ctx->func_addrs[i];
                    break;
                }
            }

            ctx->inst[ctx->inst_len++] = 19; // CALL
            ctx->inst[ctx->inst_len++] = f_addr;
            ctx->inst[ctx->inst_len++] = argc;
            ctx->inst[ctx->inst_len++] = r;
            for (int i = 0; i < argc; i++) ctx->inst[ctx->inst_len++] = arg_regs[i];
            return r;
        }

        int v = get_var_index(ctx, name);
        if (r < MAX_REGS && v < MAX_VARS) g_reg_str_idx[r] = g_var_str_idx[v];
        ctx->inst[ctx->inst_len++] = 2; // LOAD_VAR
        ctx->inst[ctx->inst_len++] = r;
        ctx->inst[ctx->inst_len++] = v;
        return r;
    }
    if (lex->cur.type == TOK_LPAREN) {
        lex_advance(lex);
        int res = parse_expression(lex, ctx);
        if (lex->cur.type == TOK_RPAREN) lex_advance(lex);
        return res;
    }
    return r;
}

static int parse_multiplication(Lexer* lex, CompilerContext* ctx) {
    int left = parse_primary(lex, ctx);
    while (lex->cur.type == TOK_STAR || lex->cur.type == TOK_SLASH || lex->cur.type == TOK_PERCENT) {
        TokenType op = lex->cur.type;
        lex_advance(lex);
        int right = parse_primary(lex, ctx);
        int res = ctx->next_reg++;
        ctx->inst[ctx->inst_len++] = (op == TOK_STAR) ? 6 : (op == TOK_SLASH) ? 7 : 8;
        ctx->inst[ctx->inst_len++] = res;
        ctx->inst[ctx->inst_len++] = left;
        ctx->inst[ctx->inst_len++] = right;
        left = res;
    }
    return left;
}

static int parse_addition(Lexer* lex, CompilerContext* ctx) {
    int left = parse_multiplication(lex, ctx);
    while (lex->cur.type == TOK_PLUS || lex->cur.type == TOK_MINUS) {
        TokenType op = lex->cur.type;
        lex_advance(lex);
        int right = parse_multiplication(lex, ctx);
        int res = ctx->next_reg++;
        ctx->inst[ctx->inst_len++] = (op == TOK_PLUS) ? 4 : 5;
        ctx->inst[ctx->inst_len++] = res;
        ctx->inst[ctx->inst_len++] = left;
        ctx->inst[ctx->inst_len++] = right;
        left = res;
    }
    return left;
}

static int parse_comparison(Lexer* lex, CompilerContext* ctx) {
    int left = parse_addition(lex, ctx);
    while (lex->cur.type >= TOK_EQEQ && lex->cur.type <= TOK_GTEQ) {
        TokenType op = lex->cur.type;
        lex_advance(lex);
        int right = parse_addition(lex, ctx);
        int res = ctx->next_reg++;
        int opcode = 9;
        if (op == TOK_NOTEQ) opcode = 10;
        else if (op == TOK_LT) opcode = 11;
        else if (op == TOK_GT) opcode = 12;
        else if (op == TOK_LTEQ) opcode = 13;
        else if (op == TOK_GTEQ) opcode = 14;
        ctx->inst[ctx->inst_len++] = opcode;
        ctx->inst[ctx->inst_len++] = res;
        ctx->inst[ctx->inst_len++] = left;
        ctx->inst[ctx->inst_len++] = right;
        left = res;
    }
    return left;
}

static int parse_expression(Lexer* lex, CompilerContext* ctx) {
    return parse_comparison(lex, ctx);
}

/* Statement Parser */
static void parse_statement(Lexer* lex, CompilerContext* ctx);

static void parse_block(Lexer* lex, CompilerContext* ctx) {
    while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
    while (lex->cur.type != TOK_EOF &&
           lex->cur.type != TOK_KW_ALT &&
           lex->cur.type != TOK_KW_OTHERWISE &&
           lex->cur.type != TOK_KW_EMIT) {
        parse_statement(lex, ctx);
        while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
        // Break out on dedicated construct boundaries
        if (lex->cur.type == TOK_KW_ALT || lex->cur.type == TOK_KW_OTHERWISE) break;
    }
}

static void parse_statement(Lexer* lex, CompilerContext* ctx) {
    while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
    if (lex->cur.type == TOK_EOF) return;

    if (lex->cur.type == TOK_KW_SAY) {
        lex_advance(lex);
        if (lex->cur.type == TOK_STRING) {
            int s = add_str_const(ctx, lex->cur.text);
            ctx->inst[ctx->inst_len++] = 21; // PRINT
            ctx->inst[ctx->inst_len++] = 1;  // is_str
            ctx->inst[ctx->inst_len++] = s;
            lex_advance(lex);
        } else {
            int r = parse_expression(lex, ctx);
            ctx->inst[ctx->inst_len++] = 21; // PRINT
            if (r < MAX_REGS && g_reg_str_idx[r] >= 0) {
                ctx->inst[ctx->inst_len++] = 1;  // is_str
                ctx->inst[ctx->inst_len++] = g_reg_str_idx[r];
            } else {
                ctx->inst[ctx->inst_len++] = 0;  // is_num
                ctx->inst[ctx->inst_len++] = r;
            }
        }
        return;
    }

    if (lex->cur.type == TOK_KW_LOCK || lex->cur.type == TOK_KW_SHIFT) {
        lex_advance(lex);
        if (lex->cur.type == TOK_IDENT) {
            char name[64];
            strncpy(name, lex->cur.text, 63);
            name[63] = '\0';
            lex_advance(lex);
            if (lex->cur.type == TOK_EQUAL) {
                lex_advance(lex);
                int r = parse_expression(lex, ctx);
                int v = get_var_index(ctx, name);
                if (v < MAX_VARS && r < MAX_REGS) g_var_str_idx[v] = g_reg_str_idx[r];
                ctx->inst[ctx->inst_len++] = 3; // STORE_VAR
                ctx->inst[ctx->inst_len++] = v;
                ctx->inst[ctx->inst_len++] = r;
            }
        }
        return;
    }

    if (lex->cur.type == TOK_KW_ACT) {
        lex_advance(lex);
        if (lex->cur.type == TOK_IDENT) {
            char fname[64];
            strncpy(fname, lex->cur.text, 63);
            fname[63] = '\0';
            lex_advance(lex);

            int jump_over_ip = ctx->inst_len;
            ctx->inst[ctx->inst_len++] = 15; // JUMP over function body
            ctx->inst[ctx->inst_len++] = 0;  // placeholder

            int fn_addr = ctx->inst_len;
            if (ctx->func_count < 64) {
                strncpy(ctx->func_names[ctx->func_count], fname, 63);
                ctx->func_addrs[ctx->func_count] = fn_addr;
                ctx->func_count++;
            }

            char params[8][64];
            int pcount = 0;
            if (lex->cur.type == TOK_LPAREN) {
                lex_advance(lex);
                while (lex->cur.type == TOK_IDENT && pcount < 8) {
                    strncpy(params[pcount++], lex->cur.text, 63);
                    lex_advance(lex);
                    if (lex->cur.type == TOK_COMMA) lex_advance(lex);
                }
                if (lex->cur.type == TOK_RPAREN) lex_advance(lex);
            }

            for (int i = 0; i < pcount; i++) {
                int v = get_var_index(ctx, params[i]);
                ctx->inst[ctx->inst_len++] = 3; // STORE_VAR
                ctx->inst[ctx->inst_len++] = v;
                ctx->inst[ctx->inst_len++] = i; // passed in regs 0..n
            }

            while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
            while (lex->cur.type != TOK_KW_EMIT && lex->cur.type != TOK_EOF) {
                parse_statement(lex, ctx);
                while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
            }

            if (lex->cur.type == TOK_KW_EMIT) {
                lex_advance(lex);
                int r = parse_expression(lex, ctx);
                ctx->inst[ctx->inst_len++] = 20; // RETURN
                ctx->inst[ctx->inst_len++] = r;
            } else {
                int r = ctx->next_reg++;
                int c = add_num_const(ctx, 0.0);
                ctx->inst[ctx->inst_len++] = 1;
                ctx->inst[ctx->inst_len++] = r;
                ctx->inst[ctx->inst_len++] = c;
                ctx->inst[ctx->inst_len++] = 20;
                ctx->inst[ctx->inst_len++] = r;
            }

            ctx->inst[jump_over_ip + 1] = ctx->inst_len;
        }
        return;
    }

    if (lex->cur.type == TOK_KW_SPIN) {
        lex_advance(lex);
        int loop_start = ctx->inst_len;
        int cond_reg = parse_expression(lex, ctx);

        int jump_false_ip = ctx->inst_len;
        ctx->inst[ctx->inst_len++] = 16; // JUMP_IF_FALSE
        ctx->inst[ctx->inst_len++] = cond_reg;
        ctx->inst[ctx->inst_len++] = 0;  // placeholder

        while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
        while (lex->cur.type != TOK_EOF && lex->cur.type != TOK_KW_SPIN &&
               lex->cur.type != TOK_KW_ACT && lex->cur.type != TOK_KW_HALT) {
            parse_statement(lex, ctx);
            while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
            if (lex->cur.type == TOK_IDENT || lex->cur.type == TOK_KW_SAY ||
                lex->cur.type == TOK_KW_LOCK || lex->cur.type == TOK_KW_SHIFT) {
                // Keep parsing body statements
            } else {
                break;
            }
        }

        ctx->inst[ctx->inst_len++] = 15; // JUMP back to loop start
        ctx->inst[ctx->inst_len++] = loop_start;
        ctx->inst[jump_false_ip + 2] = ctx->inst_len;
        return;
    }

    if (lex->cur.type == TOK_KW_PICK) {
        lex_advance(lex);
        int cond_reg = parse_expression(lex, ctx);
        int jump_false_ip = ctx->inst_len;
        ctx->inst[ctx->inst_len++] = 16; // JUMP_IF_FALSE
        ctx->inst[ctx->inst_len++] = cond_reg;
        ctx->inst[ctx->inst_len++] = 0;

        while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
        parse_statement(lex, ctx);

        int jump_end_ip = ctx->inst_len;
        ctx->inst[ctx->inst_len++] = 15; // JUMP to end
        ctx->inst[ctx->inst_len++] = 0;
        ctx->inst[jump_false_ip + 2] = ctx->inst_len;

        while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
        if (lex->cur.type == TOK_KW_OTHERWISE) {
            lex_advance(lex);
            while (lex->cur.type == TOK_NEWLINE) lex_advance(lex);
            parse_statement(lex, ctx);
        }
        ctx->inst[jump_end_ip + 1] = ctx->inst_len;
        return;
    }

    if (lex->cur.type == TOK_IDENT) {
        char name[64];
        strncpy(name, lex->cur.text, 63);
        name[63] = '\0';
        lex_advance(lex);

        if (lex->cur.type == TOK_EQUAL) {
            lex_advance(lex);
            int r = parse_expression(lex, ctx);
            int v = get_var_index(ctx, name);
            if (v < MAX_VARS && r < MAX_REGS) g_var_str_idx[v] = g_reg_str_idx[r];
            ctx->inst[ctx->inst_len++] = 3; // STORE_VAR
            ctx->inst[ctx->inst_len++] = v;
            ctx->inst[ctx->inst_len++] = r;
            return;
        }
    }

    if (lex->cur.type == TOK_KW_HALT) {
        lex_advance(lex);
        ctx->inst[ctx->inst_len++] = 17; // HALT
        return;
    }

    // Skip unhandled tokens gracefully
    lex_advance(lex);
}

/* ============================================================================
 * Exported WebAssembly Entrypoint
 * ============================================================================ */
EMSCRIPTEN_EXPORT
const char* run_foxvc(const char* source_code) {
    out_reset();
    init_str_tracking();

    if (!source_code || !*source_code) {
        out_puts("(Empty program)");
        return g_out_buf;
    }

    CompilerContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    Lexer lex;
    lex.src = source_code;
    lex.pos = 0;
    lex.line = 1;
    lex_advance(&lex);

    while (lex.cur.type != TOK_EOF) {
        parse_statement(&lex, &ctx);
        while (lex.cur.type == TOK_NEWLINE) lex_advance(&lex);
    }

    // Append final HALT instruction
    ctx.inst[ctx.inst_len++] = 17;

    const char* str_ptrs[MAX_CONSTS];
    for (int i = 0; i < ctx.str_consts_len; i++) {
        str_ptrs[i] = ctx.str_consts[i];
    }

    run_bytecode(
        ctx.inst, ctx.inst_len,
        ctx.num_consts, ctx.num_consts_len,
        str_ptrs, ctx.str_consts_len
    );

    if (g_out_pos == 0) {
        out_puts("(Program completed cleanly with no output)");
    }

    return g_out_buf;
}

#ifndef __EMSCRIPTEN__
/* Local host compilation testing entrypoint */
int main(int argc, char** argv) {
    const char* test_code =
        "lock message = \"Hello from FoxVC WebAssembly Engine!\"\n"
        "say message\n"
        "\n"
        "act fibonacci(n)\n"
        "    lock a = 0\n"
        "    lock b = 1\n"
        "    lock i = 0\n"
        "    spin i < n\n"
        "        lock temp = a + b\n"
        "        a = b\n"
        "        b = temp\n"
        "        i = i + 1\n"
        "    emit a\n"
        "\n"
        "lock res = fibonacci(10)\n"
        "say res\n";

    printf("--- Running FoxVC WASM Bridge Test ---\n");
    const char* output = run_foxvc(test_code);
    printf("%s", output);
    printf("--- Test Finished ---\n");
    return 0;
}
#endif
