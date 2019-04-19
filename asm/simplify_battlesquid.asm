.open "sys/main.dol"
.org 0x800C1FEC
  b restore_seed

; Make it so RNG is updated after pressing A in the sinking ship minigame
; only if the last ship was shot down
.org 0x800C2370
  b sinking_ships_attack_hook
.close
