
.macro padded_string string, max
  1:
    .ascii "\string"
  2:
    .ifle \max - (2b - 1b)
      .error "String too long"
    .endif

    .ifgt \max - (2b - 1b)
      .zero \max - (2b - 1b)
    .endif
.endm
