
; Normally the Great Fairies will give you the next tier max-up upgrade, depending on what you currently have.
; So if you already got the 1000 Rupee Wallet from one Great Fairy, the second one will give you the 5000 Rupee Wallet, regardless of the order you reach them in.
; This patch changes it so they always give a constant item even if you already have it, so that the item can be randomized safely.

.org 0x217C

; Check this Great Fairy's index to determine what item to give.
cmpwi r0, 1
blt 0x21B8 ; 0, Northern Fairy Island Great Fairy. Give 1000 Rupee Wallet.
beq 0x21C4 ; 1, Outset Island Great Fairy. Give 5000 Rupee Wallet.
cmpwi r0, 3
blt 0x21E4 ; 2, Eastern Fairy Island Great Fairy. Give 60 Bomb Bomb Bag.
beq 0x21F0 ; 3, Southern Fairy Island Great Fairy. Give 99 Bomb Bomb Bag.
cmpwi r0, 5
blt 0x2210 ; 4, Western Fairy Island Great Fairy. Give 60 Arrow Quiver.
beq 0x221C ; 5, Thorned Fairy Island Great Fairy. Give 99 Arrow Quiver.
b 0x2228 ; Failsafe code in case the index was invalid (give a red rupee instead)
