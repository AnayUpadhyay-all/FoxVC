#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#ifdef FOX_ENABLE_RAYLIB
#include <raylib.h>
#endif

#define MAX_REGS 256
#define MAX_VARS 512
#define MAX_CALL_STACK 1024
#define INITIAL_PACK_CAPACITY 4096
#define MAX_PACK_CAPACITY 65536

// Tiered Chained Memory Arena configuration
#define PRIMARY_ARENA_SIZE   (8 * 1024 * 1024)   // Tier 1: 8 MB static BSS arena (1 CPU cycle bump)
#define STANDBY_ARENA_SIZE   (8 * 1024 * 1024)   // Tier 2: 8 MB pre-warmed standby BSS arena (0 cost until touched)
#define CHUNK_ARENA_SIZE     (8 * 1024 * 1024)   // Tier 3: 8 MB dynamic chained chunks
#define MAX_ARENA_CEILING    (64 * 1024 * 1024)  // Tier 4: 64 MB runaway loop memory safety ceiling

#if defined(__GNUC__) || defined(__clang__)
#define FOX_LIKELY(x)   __builtin_expect(!!(x), 1)
#define FOX_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define FOX_LIKELY(x)   (x)
#define FOX_UNLIKELY(x) (x)
#endif

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

typedef struct {
    int mold_id;
    int field_count;
    int field_keys[32];
    double field_vals[32];
} FoxObject;

// Dynamic Pack and Object Tables (Starting with static fast-path buffers)
static FoxPack heap_packs_static[INITIAL_PACK_CAPACITY];
static FoxPack* heap_packs = heap_packs_static;
static int pack_capacity = INITIAL_PACK_CAPACITY;
static int pack_count = 0;

static FoxObject heap_objects_static[INITIAL_PACK_CAPACITY];
static FoxObject* heap_objects = heap_objects_static;
static int object_capacity = INITIAL_PACK_CAPACITY;
static int object_count = 0;

// Tiered Arena Blocks
typedef struct ArenaBlock {
    char* data;
    size_t capacity;
    size_t offset;
    int is_dynamic;
    struct ArenaBlock* next;
} ArenaBlock;

static char g_primary_arena[PRIMARY_ARENA_SIZE];
static char g_standby_arena[STANDBY_ARENA_SIZE];

static ArenaBlock g_primary_block = { g_primary_arena, PRIMARY_ARENA_SIZE, 0, 0, NULL };
static ArenaBlock g_standby_block = { g_standby_arena, STANDBY_ARENA_SIZE, 0, 0, NULL };

static ArenaBlock* g_current_block = &g_primary_block;
static ArenaBlock* g_dynamic_chain = NULL;
static size_t g_total_arena_allocated = 0;
static int g_standby_used = 0;

static void reset_pack_tables(void) {
    if (heap_packs != heap_packs_static) {
        free(heap_packs);
        heap_packs = heap_packs_static;
        pack_capacity = INITIAL_PACK_CAPACITY;
    }
    pack_count = 0;

    if (heap_objects != heap_objects_static) {
        free(heap_objects);
        heap_objects = heap_objects_static;
        object_capacity = INITIAL_PACK_CAPACITY;
    }
    object_count = 0;
}

void reset_memory_arena(void) {
    // Free all dynamically chained chunks
    ArenaBlock* curr = g_dynamic_chain;
    while (curr) {
        ArenaBlock* next = curr->next;
        if (curr->data) {
            free(curr->data);
        }
        free(curr);
        curr = next;
    }
    g_dynamic_chain = NULL;

    // Reset primary and pre-warmed standby blocks
    g_primary_block.offset = 0;
    g_standby_block.offset = 0;
    g_current_block = &g_primary_block;
    g_standby_used = 0;
    g_total_arena_allocated = 0;

    // Reset dynamic pack and object tables
    reset_pack_tables();
}

static void* arena_alloc_slow(size_t aligned_size) {
    // Tier 2: Pre-Warmed Standby Arena Rollover
    // Activates in 1 instruction with zero heap syscall latency
    if (!g_standby_used) {
        g_standby_used = 1;
        g_current_block = &g_standby_block;
        if (FOX_LIKELY(g_current_block->offset + aligned_size <= g_current_block->capacity)) {
            void* ptr = (void*)(g_current_block->data + g_current_block->offset);
            g_current_block->offset += aligned_size;
            g_total_arena_allocated += aligned_size;
            return ptr;
        }
    }

    // Tier 4: Memory Safety Ceiling (64 MB)
    // Prevents runaway infinite loops from exhausting host system RAM
    if (FOX_UNLIKELY(g_total_arena_allocated + aligned_size > MAX_ARENA_CEILING)) {
        fprintf(stderr, "[FoxVC Safety Trap]: Memory ceiling reached (64 MB). Runaway loop protected.\n");
        return NULL;
    }

    // Tier 3: Dynamic Chained Arena Chunks
    size_t chunk_cap = CHUNK_ARENA_SIZE;
    if (aligned_size > chunk_cap) {
        chunk_cap = aligned_size;
    }
    if (g_total_arena_allocated + chunk_cap > MAX_ARENA_CEILING) {
        chunk_cap = MAX_ARENA_CEILING - g_total_arena_allocated;
        if (aligned_size > chunk_cap) {
            fprintf(stderr, "[FoxVC Safety Trap]: Memory ceiling reached (64 MB). Runaway loop protected.\n");
            return NULL;
        }
    }

    ArenaBlock* new_block = (ArenaBlock*)malloc(sizeof(ArenaBlock));
    if (!new_block) return NULL;
    new_block->data = (char*)malloc(chunk_cap);
    if (!new_block->data) {
        free(new_block);
        return NULL;
    }

    new_block->capacity = chunk_cap;
    new_block->offset = aligned_size;
    new_block->is_dynamic = 1;
    new_block->next = g_dynamic_chain;
    g_dynamic_chain = new_block;
    g_current_block = new_block;
    g_total_arena_allocated += aligned_size;

    return (void*)new_block->data;
}

static inline void* arena_alloc(size_t size) {
    // 8-byte alignment for 64-bit doubles
    size_t aligned_size = (size + 7) & ~((size_t)7);

    // Fast path: single pointer bump within current active block (1 CPU cycle)
    if (FOX_LIKELY(g_current_block->offset + aligned_size <= g_current_block->capacity)) {
        void* ptr = (void*)(g_current_block->data + g_current_block->offset);
        g_current_block->offset += aligned_size;
        g_total_arena_allocated += aligned_size;
        return ptr;
    }

    // Slow path: rollover to standby block or allocate dynamic chunk
    return arena_alloc_slow(aligned_size);
}

int allocate_pack(int initial_cap) {
    if (pack_count >= pack_capacity) {
        if (pack_capacity >= MAX_PACK_CAPACITY) {
            fprintf(stderr, "[FoxVC Safety Trap]: Pack table capacity limit reached (%d packs).\n", MAX_PACK_CAPACITY);
            return -1;
        }
        int new_cap = pack_capacity * 2;
        if (new_cap > MAX_PACK_CAPACITY) new_cap = MAX_PACK_CAPACITY;

        FoxPack* new_packs;
        if (heap_packs == heap_packs_static) {
            new_packs = (FoxPack*)malloc(new_cap * sizeof(FoxPack));
            if (!new_packs) return -1;
            memcpy(new_packs, heap_packs_static, pack_count * sizeof(FoxPack));
        } else {
            new_packs = (FoxPack*)realloc(heap_packs, new_cap * sizeof(FoxPack));
            if (!new_packs) return -1;
        }
        heap_packs = new_packs;
        pack_capacity = new_cap;
    }
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

static int allocate_object(int count) {
    if (object_count >= object_capacity) {
        if (object_capacity >= MAX_PACK_CAPACITY) {
            fprintf(stderr, "[FoxVC Safety Trap]: Object table capacity limit reached (%d objects).\n", MAX_PACK_CAPACITY);
            return -1;
        }
        int new_cap = object_capacity * 2;
        if (new_cap > MAX_PACK_CAPACITY) new_cap = MAX_PACK_CAPACITY;

        FoxObject* new_objs;
        if (heap_objects == heap_objects_static) {
            new_objs = (FoxObject*)malloc(new_cap * sizeof(FoxObject));
            if (!new_objs) return -1;
            memcpy(new_objs, heap_objects_static, object_count * sizeof(FoxObject));
        } else {
            new_objs = (FoxObject*)realloc(heap_objects, new_cap * sizeof(FoxObject));
            if (!new_objs) return -1;
        }
        heap_objects = new_objs;
        object_capacity = new_cap;
    }
    int oid = object_count++;
    heap_objects[oid].mold_id = 0;
    heap_objects[oid].field_count = (count > 32) ? 32 : count;
    return oid;
}

#ifdef FOX_ENABLE_RAYLIB
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
#endif

// Generic native dispatch bridge
double dispatch_native(const char* name, double* args, int argc) {
#ifdef FOX_ENABLE_RAYLIB
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
#else
    (void)name;
    (void)args;
    (void)argc;
#endif
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
#ifdef FOX_ENABLE_RAYLIB
                if (IsWindowReady()) CloseWindow();
#endif
                {
                    double ret = regs[0];
                    reset_memory_arena();
                    return ret;
                }
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

                // Tail-Call Optimization (TCO):
                // If inside a function (call_sp > 0) and the immediate next instruction is RETURN res_reg,
                // reuse the current stack frame to enable infinite recursion in O(1) stack space.
                int is_tail_call = (call_sp > 0) &&
                                   (ip + argc + 1 < inst_len) &&
                                   (inst[ip + argc] == 20) &&
                                   (inst[ip + argc + 1] == res_reg);

                if (!is_tail_call) {
                    if (call_sp >= MAX_CALL_STACK) {
                        reset_memory_arena();
                        return -999.0;
                    }
                    for (int i = 0; i < MAX_REGS; i++) call_stack[call_sp].saved_regs[i] = regs[i];
                    call_stack[call_sp].return_ip = ip + argc;
                    call_stack[call_sp].target_reg = res_reg;
                    call_sp++;
                }

                double temp[MAX_REGS];
                for (int i = 0; i < argc; i++) temp[i] = regs[inst[ip + i]];
                for (int i = 0; i < argc; i++) regs[i] = temp[i];
                ip = f_addr;
                break;
            }
            case 20: { // RETURN
                int v_reg = inst[ip++];
                double val = regs[v_reg];
                if (call_sp <= 0) {
                    reset_memory_arena();
                    return val;
                }
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
#ifdef FOX_ENABLE_RAYLIB
                if (IsWindowReady()) CloseWindow();
#endif
                {
                    double ret = regs[s];
                    reset_memory_arena();
                    return ret;
                }
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
            case 35: { // GUARD: [35, cond_reg]
                int cond_reg = inst[ip++];
                if (!regs[cond_reg]) {
                    fprintf(stderr, "FoxVM Panic: Guard assertion failed!\n");
                    reset_memory_arena();
                    return -1.0;
                }
                break;
            }
            case 36: { // BUILD_PACK / MOLD_NEW: [36, dst_reg, field_count, k0, v0_reg, k1, v1_reg...]
                int dst = inst[ip++];
                int count = inst[ip++];
                int oid = allocate_object(count);
                if (oid >= 0) {
                    for (int f = 0; f < count; f++) {
                        int k = inst[ip++];
                        int vr = inst[ip++];
                        if (f < 32) {
                            heap_objects[oid].field_keys[f] = k;
                            heap_objects[oid].field_vals[f] = regs[vr];
                        }
                    }
                    regs[dst] = (double)oid;
                } else {
                    ip += count * 2;
                    regs[dst] = 0.0;
                }
                break;
            }
            case 37: { // GET_MEMBER: [37, dst_reg, obj_reg, key_str_idx]
                int dst = inst[ip++];
                int obj_reg = inst[ip++];
                int key_idx = inst[ip++];
                int oid = (int)regs[obj_reg];
                double val = 0.0;
                if (oid >= 0 && oid < object_count) {
                    for (int f = 0; f < heap_objects[oid].field_count; f++) {
                        if (heap_objects[oid].field_keys[f] == key_idx) {
                            val = heap_objects[oid].field_vals[f];
                            break;
                        }
                    }
                }
                regs[dst] = val;
                break;
            }
            case 38: { // SET_MEMBER: [38, obj_reg, key_str_idx, val_reg]
                int obj_reg = inst[ip++];
                int key_idx = inst[ip++];
                int val_reg = inst[ip++];
                int oid = (int)regs[obj_reg];
                if (oid >= 0 && oid < object_count) {
                    int found = 0;
                    for (int f = 0; f < heap_objects[oid].field_count; f++) {
                        if (heap_objects[oid].field_keys[f] == key_idx) {
                            heap_objects[oid].field_vals[f] = regs[val_reg];
                            found = 1;
                            break;
                        }
                    }
                    if (!found && heap_objects[oid].field_count < 32) {
                        int f = heap_objects[oid].field_count++;
                        heap_objects[oid].field_keys[f] = key_idx;
                        heap_objects[oid].field_vals[f] = regs[val_reg];
                    }
                }
                break;
            }
            default:
                break;
        }
    }
#ifdef FOX_ENABLE_RAYLIB
    if (IsWindowReady()) CloseWindow();
#endif
    {
        double ret = regs[0];
        reset_memory_arena();
        return ret;
    }
}
