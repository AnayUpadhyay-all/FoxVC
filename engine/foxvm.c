#include <stdint.h>
#include <time.h>
#include <math.h>

typedef struct {
    int32_t op;
    int32_t a;
    int32_t b;
    int32_t c;
    double val;
} FoxInstruction;

static double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

double run_vm_c(const FoxInstruction* code, int length) {
    double regs[256] = {0.0};
    double vars[256] = {0.0};
    int ip = 0;
    double emitted = 0.0;

    while (ip < length) {
        const FoxInstruction* inst = &code[ip];
        switch (inst->op) {
            case 1:  regs[inst->a] = inst->val; break;                       // LOAD_CONST
            case 2:  regs[inst->a] = vars[inst->b]; break;                   // LOAD_VAR
            case 3:  vars[inst->a] = regs[inst->b]; break;                   // STORE_VAR
            case 4:  regs[inst->a] = regs[inst->b] + regs[inst->c]; break;   // ADD
            case 5:  regs[inst->a] = regs[inst->b] - regs[inst->c]; break;   // SUB
            case 6:  regs[inst->a] = regs[inst->b] * regs[inst->c]; break;   // MUL
            case 7:  regs[inst->a] = regs[inst->b] / regs[inst->c]; break;   // DIV
            case 8:  regs[inst->a] = fmod(regs[inst->b], regs[inst->c]); break; // MOD
            case 9:  regs[inst->a] = (regs[inst->b] == regs[inst->c]); break;// CMP_EQ
            case 10: regs[inst->a] = (regs[inst->b] != regs[inst->c]); break;// CMP_NE
            case 11: regs[inst->a] = (regs[inst->b] < regs[inst->c]); break; // CMP_LT
            case 12: regs[inst->a] = (regs[inst->b] > regs[inst->c]); break; // CMP_GT
            case 13: regs[inst->a] = (regs[inst->b] <= regs[inst->c]); break;// CMP_LE
            case 14: regs[inst->a] = (regs[inst->b] >= regs[inst->c]); break;// CMP_GE
            case 15: regs[inst->a] = (regs[inst->b] == 0.0) ? 1.0 : 0.0; break; // LOGIC_NOT
            case 16: ip = inst->a; continue;                                 // JUMP
            case 17:                                                         // JUMP_IF_FALSE
                if (regs[inst->a] == 0.0) { ip = inst->b; continue; }
                break;
            case 18: regs[inst->a] = get_time_sec(); break;                  // GET_TIME
            case 19: emitted = regs[inst->a]; break;                         // EMIT
            case 20: return emitted;                                         // HALT
            default: break;
        }
        ip++;
    }
    return emitted;
}
