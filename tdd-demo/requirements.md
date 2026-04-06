# Password Validator — Requirements

## Overview
Build a password validator that checks whether a password meets company security policy. Returns whether the password is valid and a list of which rules it violated.

## Function Signature
```ts
function validatePassword(password: string): {
  valid: boolean;
  errors: string[];
}
```

## Rules

1. Must be at least **8 characters** long — error: "Must be at least 8 characters"
2. Must contain at least **one uppercase letter** — error: "Must contain an uppercase letter"
3. Must contain at least **one number** — error: "Must contain a number"
4. Must contain at least **one special character** (!@#$%^&*) — error: "Must contain a special character"

## Examples

| Password | Valid | Errors |
|----------|-------|--------|
| `"MyPass1!"` | true | [] |
| `"short"` | false | ["Must be at least 8 characters", "Must contain an uppercase letter", "Must contain a number", "Must contain a special character"] |
| `"alllowercase1!"` | false | ["Must contain an uppercase letter"] |
| `""` (empty) | false | all four errors |
