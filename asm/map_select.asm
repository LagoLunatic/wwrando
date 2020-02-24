
; Enter the debug map select game mode if the player is holding down a certain button combination at any point that Link is loaded.
.open "sys/main.dol"
.org 0x80234BF8 ; In dScnPly_Draw
  b check_open_map_select
.close
