
; Changes the function that initializes the sea chart when starting a new game so that the whole chart has been drawn out.
.open "sys/main.dol"
.org 0x8005B2CC
  li r4, 1
.close
