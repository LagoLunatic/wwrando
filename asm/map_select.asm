
; Enter the debug map select game mode if the player is holding down the Y button during certain transitions.
.open "sys/main.dol"
.org 0x802322E8 ; In dScnName_c::changeGameScene
  ; For loading a save file
  bl change_game_state_check_enter_debug_map_select
.org 0x80234CCC ; In dScnPly_Draw
  ; For changing stages while ingame
  bl change_game_state_check_enter_debug_map_select
.close
