
.macro padded_string string, max

before_padded_string:
.ascii "\string"
after_padded_string:
.iflt \max - (after_padded_string - before_padded_string)
.error "String too long"
.endif

.ifgt \max - (after_padded_string - before_padded_string)
.zero \max - (after_padded_string - before_padded_string)
.endif

.endm
