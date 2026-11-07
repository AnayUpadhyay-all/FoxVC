# Formal Grammar Specification for FoxVC (v1.0.0)

This document contains the official **Extended Backus-Naur Form (EBNF)** grammar specification for the FoxVC programming language.

---

## 1. Lexical Grammar (Tokens)

```ebnf
(* 25 Official Keywords *)
KEYWORD         = "act" | "emit" | "mold" | "pack" | "pick" | "alt" | "otherwise"
                | "pulse" | "cycle" | "spin" | "halt" | "skip" | "say" | "ask"
                | "guard" | "trap" | "fuse" | "lock" | "shift" | "blank"
                | "aye" | "nay" | "also" | "either" | "deny" ;

IDENTIFIER      = ( LETTER | "_" ) { LETTER | DIGIT | "_" } ;
LETTER          = "a" ... "z" | "A" ... "Z" ;
DIGIT           = "0" ... "9" ;

NUMBER          = [ "-" ] DIGIT { DIGIT } [ "." DIGIT { DIGIT } ] ;
STRING          = '"' { ANY_CHAR_EXCEPT_QUOTE | ESCAPE_SEQ } '"' ;
BOOLEAN         = "aye" | "nay" ;
NULL_LITERAL    = "blank" ;

COMMENT         = "#" { ANY_CHAR_EXCEPT_NEWLINE } NEWLINE ;
NEWLINE         = "\n" | "\r\n" ;
```

---

## 2. Syntactic Grammar (EBNF)

```ebnf
Program         = { Statement | NEWLINE } ;

Statement       = VarDecl
                | Assignment
                | FunctionDecl
                | EmitStmt
                | MoldDecl
                | PickStmt
                | CycleStmt
                | SpinStmt
                | PulseStmt
                | GuardStmt
                | TrapStmt
                | SayStmt
                | FuseStmt
                | "halt"
                | "skip"
                | Expression ;

(* Variables & Constants *)
VarDecl         = [ "lock" ] IDENTIFIER "=" Expression ;
Assignment      = AccessExpr ( "=" | "+=" | "-=" | "*=" | "/=" ) Expression ;

(* Subroutines & Returns *)
FunctionDecl    = "act" IDENTIFIER "(" [ ParameterList ] ")" Block ;
ParameterList   = IDENTIFIER { [ "," ] IDENTIFIER } ;
EmitStmt        = "emit" [ Expression ] ;

(* Blueprints / Schemas *)
MoldDecl        = "mold" IDENTIFIER "{" { MoldField } "}" ;
MoldField       = IDENTIFIER ":" Expression [ NEWLINE ] ;

(* Conditionals *)
PickStmt        = "pick" Expression Block
                  { "alt" Expression Block }
                  [ "otherwise" Block ] ;

(* Loops *)
CycleStmt       = "cycle" IDENTIFIER Expression Block ;
SpinStmt        = "spin" Expression Block ;
PulseStmt       = "pulse" IDENTIFIER Block ;

(* Defensive Assertions & Traps *)
GuardStmt       = "guard" Expression ;
TrapStmt        = "trap" Block "otherwise" Block ;

(* I/O and Modules *)
SayStmt         = "say" Expression ;
FuseStmt        = "fuse" ( STRING | IDENTIFIER ) ;

(* Code Blocks: 4-space indentation *)
Block           = NEWLINE INDENT { Statement } DEDENT ;
```

---

## 3. Expressions & Precedence

```ebnf
Expression      = LogicalOr ;

LogicalOr       = LogicalAnd { "either" LogicalAnd } ;
LogicalAnd      = Equality { "also" Equality } ;
Equality        = Comparison { ( "==" | "!=" ) Comparison } ;
Comparison      = BitShift { ( "<" | "<=" | ">" | ">=" ) BitShift } ;
BitShift        = Additive { "shift" Additive } ;
Additive        = Multiplicative { ( "+" | "-" ) Multiplicative } ;
Multiplicative  = Unary { ( "*" | "/" | "%" ) Unary } ;

Unary           = ( "deny" | "-" | "+" ) Unary
                | Primary ;

Primary         = NUMBER
                | STRING
                | BOOLEAN
                | NULL_LITERAL
                | PackLiteral
                | ListLiteral
                | "ask" Expression
                | AccessExpr
                | "(" Expression ")" ;

PackLiteral     = "pack" "{" { PackEntry } "}" ;
PackEntry       = ( IDENTIFIER | STRING ) ":" Expression [ [ "," ] NEWLINE ] ;

ListLiteral     = "[" [ Expression { [ "," ] Expression } ] "]" ;

AccessExpr      = IDENTIFIER { CallSuffix | IndexSuffix | MemberSuffix } ;
CallSuffix      = "(" [ ArgList ] ")" ;
ArgList         = Expression { [ "," ] Expression } ;
IndexSuffix     = "[" Expression "]" ;
MemberSuffix    = "." IDENTIFIER ;
```

---

## 4. Punctuation Philosophy

FoxVC rejects extraneous syntactic punctuation:
- **Zero semicolons:** Statements are delimited strictly by newlines.
- **Minimal commas:** Function parameters, list elements, and pack entries are separated naturally by whitespace and newlines.
- **Keywords as Operators:** Boolean logic uses standard natural words (`also`, `either`, `deny`) instead of symbols (`&&`, `||`, `!`).
