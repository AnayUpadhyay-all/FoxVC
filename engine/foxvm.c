#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <raylib.h>

#define MAX_REGS 256
#define MAX_VARS 512
#define MAX_CALL_STACK 1024
#define MAX_PACKS 4096
#define ARENA_SIZE_BYTES (8 * 1024 * 1024) // 8 MB linear arena

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

void reset_memory_arena(void) {
    g_arena_offset = 0;
    pack_count = 0;
}

static void* arena_alloc(size_t size) {
    // 8-byte alignment for doubles
    size_t aligned_size = (size + 7) & ~((size_t)7);
    if (g_arena_offset + aligned_size > ARENA_SIZE_BYTES) {
        return NULL;
    }
    void* ptr = (void*)&g_memory_arena[g_arena_offset];
    g_arena_offset += aligned_size;
    return ptr;
}

int allocate_pack(int initial_cap) {
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

static Color get_color_from_code(int col) {
    switch (col) {
        case 1: return ORANGE;
        case 2: return GREEN;
        case 3: return RED;
        case 4: return BLUE;
        case 5: return YELLOW;
        case 6: return PURPLE;
        case 7: return BLACK;
        case 8: return WHITE;
        default: return RAYWHITE;
    }
}

// Generic native dispatch bridge
double dispatch_native(const char* name, double* args, int argc) {
    if (strcmp(name, "win_open") == 0) {
        int w = (argc > 0) ? (int)args[0] : 800;
        int h = (argc > 1) ? (int)args[1] : 600;
        InitWindow(w, h, "FoxVC Game [Native FFI]");
        SetTargetFPS(60);
        return 1.0;
    } else if (strcmp(name, "win_running") == 0) {
        return WindowShouldClose() ? 0.0 : 1.0;
    } else if (strcmp(name, "frame_start") == 0) {
        BeginDrawing();
        ClearBackground((Color){15, 18, 25, 255});
        return 1.0;
    } else if (strcmp(name, "frame_end") == 0) {
        EndDrawing();
        return 1.0;
    } else if (strcmp(name, "draw_rect") == 0) {
        int x = (int)args[0]; int y = (int)args[1];
        int w = (int)args[2]; int h = (int)args[3];
        int col = (argc > 4) ? (int)args[4] : 1;
        DrawRectangle(x, y, w, h, get_color_from_code(col));
        return 1.0;
    } else if (strcmp(name, "draw_circle") == 0) {
        int cx = (int)args[0]; int cy = (int)args[1];
        float radius = (float)args[2];
        int col = (argc > 3) ? (int)args[3] : 1;
        DrawCircle(cx, cy, radius, get_color_from_code(col));
        return 1.0;
    } else if (strcmp(name, "draw_line") == 0) {
        int x1 = (int)args[0]; int y1 = (int)args[1];
        int x2 = (int)args[2]; int y2 = (int)args[3];
        int col = (argc > 4) ? (int)args[4] : 1;
        DrawLine(x1, y1, x2, y2, get_color_from_code(col));
        return 1.0;
    } else if (strcmp(name, "key_down") == 0) {
        int key = (int)args[0];
        return IsKeyDown(key) ? 1.0 : 0.0;
    } else if (strcmp(name, "key_pressed") == 0) {
        int key = (int)args[0];
        return IsKeyPressed(key) ? 1.0 : 0.0;
    } else if (strcmp(name, "mouse_x") == 0) {
        return (double)GetMouseX();
    } else if (strcmp(name, "mouse_y") == 0) {
        return (double)GetMouseY();
    } else if (strcmp(name, "mouse_down") == 0) {
        int btn = (argc > 0) ? (int)args[0] : 0;
        return IsMouseButtonDown(btn) ? 1.0 : 0.0;
    } else if (strcmp(name, "mouse_pressed") == 0) {
        int btn = (argc > 0) ? (int)args[0] : 0;
        return IsMouseButtonPressed(btn) ? 1.0 : 0.0;
    } else if (strcmp(name, "get_fps") == 0) {
        return (double)GetFPS();
    } else if (strcmp(name, "set_fps") == 0) {
        SetTargetFPS((int)args[0]);
        return 1.0;
    }
    return 0.0;
}

double run_bytecode(int* inst, int inst_len, double* num_consts, int num_consts_len, const char** str_consts, int str_consts_len) {
    reset_memory_arena();
    double regs[MAX_REGS] = {0.0};
    double vars[MAX_VARS] = {0.0};
    FoxFrame call_stack[MAX_CALL_STACK];
    int call_sp = 0;
    int ip = 0;

    while (ip < inst_len) {
        int op = inst[ip++];
        switch (op) {
            case 1: { // LOAD_CONST
                int r = inst[ip++]; int c = inst[ip++];
                regs[r] = num_consts[c];
                break;
            }
            case 2: { // LOAD_VAR: [2, dst_reg, var_idx]
                int d = inst[ip++]; int v = inst[ip++];
                regs[d] = (v >= 0 && v < MAX_VARS) ? vars[v] : 0.0;
                break;
            }
            case 3: { // STORE_VAR: [3, var_idx, src_reg]
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
                int cond_reg = inst[ip++];
                int target = inst[ip++];
                if (regs[cond_reg] == 0.0) ip = target;
                break;
            }
            case 17: { // HALT
                if (IsWindowReady()) CloseWindow();
                return regs[0];
            }
            case 18: { // GET_TIME
                int d = inst[ip++];
                struct timespec ts;
                clock_gettime(CLOCK_MONOTONIC, &ts);
                regs[d] = (double)ts.tv_sec + ((double)ts.tv_nsec / 1e9);
                break;
            }
            case 19: { // CALL
                int f_addr = inst[ip++];
                int argc = inst[ip++];
                int res_reg = inst[ip++];
                if (call_sp >= MAX_CALL_STACK) return -999.0;
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
            case 21: { // PRINT
                int is_str = inst[ip++];
                int idx = inst[ip++];
                if (is_str) {
                    if (str_consts && idx < str_consts_len) printf("%s\n", str_consts[idx]);
                } else {
                    printf("%g\n", regs[idx]);
                }
                fflush(stdout);
                break;
            }
            case 22: { // EMIT
                int s = inst[ip++];
                if (IsWindowReady()) CloseWindow();
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
            case 27: { // RND
                int d = inst[ip++];
                regs[d] = (double)rand() / (double)RAND_MAX;
                break;
            }
            case 28: { // PACK_NEW: [28, cap_idx, dst_reg, count, elem0_reg, elem1_reg...]
                int cap_idx = inst[ip++];
                int dst = inst[ip++];
                int count = inst[ip++];
                int cap = count > 0 ? count : 16;
                if (num_consts && cap_idx >= 0 && cap_idx < num_consts_len) {
                    int c = (int)num_consts[cap_idx];
                    if (c > cap) cap = c;
                }
                int pid = allocate_pack(cap);
                regs[dst] = (double)pid;
                if (pid >= 0 && pid < pack_count) {
                    heap_packs[pid].size = count;
                    for (int i = 0; i < count; i++) {
                        int r = inst[ip++];
                        if (i < heap_packs[pid].capacity) {
                            heap_packs[pid].data[i] = regs[r];
                        }
                    }
                } else {
                    ip += count;
                }
                break;
            }
            case 29: { // PACK_GET: [29, dst_reg, pack_id_reg, idx_reg]
                int dst = inst[ip++]; int pid_reg = inst[ip++]; int idx_reg = inst[ip++];
                int pid = (int)regs[pid_reg]; int idx = (int)regs[idx_reg];
                if (pid >= 0 && pid < pack_count && idx >= 0 && idx < heap_packs[pid].capacity) {
                    regs[dst] = heap_packs[pid].data[idx];
                } else {
                    regs[dst] = 0.0;
                }
                break;
            }
            case 30: { // PACK_SET: [30, pack_id_reg, idx_reg, val_reg]
                int pid_reg = inst[ip++]; int idx_reg = inst[ip++]; int val_reg = inst[ip++];
                int pid = (int)regs[pid_reg]; int idx = (int)regs[idx_reg];
                if (pid >= 0 && pid < pack_count && idx >= 0 && idx < heap_packs[pid].capacity) {
                    heap_packs[pid].data[idx] = regs[val_reg];
                }
                break;
            }
            case 31: { // BIND_CALL: [31, str_idx, argc, dst_reg, arg0, arg1...]
                int s_idx = inst[ip++];
                int argc = inst[ip++];
                int dst = inst[ip++];
                const char* fn_name = (str_consts && s_idx < str_consts_len) ? str_consts[s_idx] : "";
                double call_args[MAX_REGS];
                for (int i = 0; i < argc; i++) {
                    call_args[i] = regs[inst[ip++]];
                }
                regs[dst] = dispatch_native(fn_name, call_args, argc);
                break;
            }
            default:
                break;
        }
    }
    if (IsWindowReady()) CloseWindow();
    return regs[0];
}
