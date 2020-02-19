
; Enter the debug map select game mode if the player is holding down the Y button during certain transitions.
.open "sys/main.dol"
.org 0x80234C0C ; In dScnPly_Draw
  b check_open_map_select
.close
