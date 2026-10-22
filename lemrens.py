import argparse
import asyncio
import base64
import glob
import io
import json
import logging
import math
import os
import selectors
import shutil
import subprocess
import tempfile
import sys
from getpass import getpass
import textwrap
import time
import threading
import zlib
from fractions import Fraction
from pathlib import Path

from wand.color import Color
from wand.drawing import Drawing
from wand.exceptions import WandException
from wand.image import Image

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import (
    TelegramError,
    TimedOut,
    NetworkError,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Lemrens terminal palette (ANSI; degrades gracefully on most Termux terminals)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[97m"
APP_NAME = "Lemrens"

BANNER_WIDTH = 80
BANNER_HEIGHT = 21
BANNER_FPS = (30 / 1)
BANNER_MODE = 'sharp'
BANNER_FRAME_COUNT = 82
BANNER_BYTES_PER_CELL = 4

BANNER_PAYLOAD = (
    'c-rjU3B0{~RTuuUfQmvyoH8elKg+W_WTu(NHeDnulmrn8G|3z;mZpMuF|Pw4coFY4?gdFGyBCNQ92+!&v_T4Oo}|I%dD6-'
    '>E3N+Py<XqX^ZM@R?0tsca2@)e*Xw!hefHUB@8?<1`mXO<pU)aj{^sBOn<w+}xBvFvUXH)@xBk}2U-'
    '>J4WqJMY{@uU39De`nfBmnY{GGq^cl!7T|KJ~-{D=SWA5Q-7|NXy??e~7~_a1-'
    'xr+@nKM}5>s9e?CUe&q4{z2Ez7|MZ{!)2H>f)1UmwpX|@A&pG`c|Koq0{H4G2m$qN|m0!92@-'
    'P4L?dxCv`u_a?{@?%m>HqmZ|L637{jdLZ@}occqbL9AKmDhZfBSF$?a6=qkN>g%=O6#$e|%Ekaq_SJ)xSFVkstYylYjXy|K-'
    'UK|L_l={EL6_FPzuuPyEDB^mqB&5B}f}_PM^}9q;Jl@BO{Mw;ccQAO6EW^7{|{&=2h#&c*A#@1OqDe|qLv%ggsT{>I<<8-'
    '2_&BS+_wb0D*S_Rs!VUlY0g=l}elw+}q<z~*B=_G8KG__2?D?D5Ba+{YdN=HL9AkAKat`86m1^}qhtz9#a0)0^J3{g!X}mj1tzM?'
    'e1afBw(6-}<fJy8YrW{^HH=`dz<k`+I-y@7>;Y*InCh`lfF>`SXAN&-'
    'eHLlYjD0$g1xFIsUtU_wV|5^7^qK`!PqKlh^+D|Nh_kKIi81&m7)6AN$_pa9`Y`^|8JmWRiPA{^aiXNB`&_EyuV9_r1@pu4Q}gz4'
    'sn}#7BI@@uMI8XtFx~^}qhtAOFVR_#2O(_{1k3fB1)g`0=m(wZHZx*FsO~aZ~zsI`q|Rxz^>i|MuVhoBO)`Q-'
    'A7DZU68e{=?g^`I@iU-g)Pp+b{gWFWkQ5B`?{2<2QaI-'
    '935R+unBam;dr#?(6*b|Nh^fkm29|`+wiLo|Yb47yY?E^;199I(*f`J@UEx4)The=;Ocs*Z;cj!>psZFS!TaQ|qer=<C1!>yI~^&'
    'Gw})ed*?z&wS?bulses?)XVhdeZTByKVVB{_&4*xz_7h+by5EmZP8d^M2m(Lmu*wMJG$owr_aD8)iM-'
    'cbts>@AI-A+-ve9%kTgG@9*m=`ECFBAOGVm$G5)qt-aRWqyPCo|L3XCckdnl<-'
    'h!wy@&TW%69Zo_p%RqKI=NU(WkYXW?B84fAepady%zTpLzW5@BZ$a(yPAqzxWsb;?XbtrN8v}LqGIGkAK5&_zg$oSdVT0KIUUS=I'
    'DLj_kFkZzpnkb-gm8JHy@in^oRb?$&lgkyS>}HwQRlqxW_$i^VMJd)mt+0y>;$e=UCTvGRu>ml?=CUeB&EWe&7dwVEbqO%%3^=vw'
    '!x_($Vd=ecQL4_}%)i>tR#b(9<9P@gF~Pu)B`Psn%A%_rS5pDhGQ!%Pe|oZy4)<Eq86(`|rO$I&u7nM?AtcANl#f5B$KR5B}f}KK'
    'j+a`d1&7e2+iu!#?cj13usbj&Hl|w&UOOTYk%0cJpyu|FikJulu^qJ@?#m{9f<%UhBUft&Zc9lauXtfA@E9%T_xd_iy{1-}#-'
    'JKkx_s!1jB-'
    '=X<ta`?X(t{IG{TZ2L$5=pSu6Yd;z~(DFG)HkUbCR`Wq_S?~14ca^+O={}uhw|?jE{GGjbPV13u`kH>(FZ*RjrI$x_?MLtZ-tXP='
    '{1w0ASM=k1yvKVS{gPkuOOD>@o!+VC@$-'
    'NF&!6RTNT##A)_=Qgde8C4fBeUL+^~;jFE`JB{_|ba@w>dsyBybd_u8#J<>W8?g}>19yFuBVj(zXoL0+|QEr;)}HNJiAYhT-'
    'cw+@_>b@%7~+@I^~pohQc7yY86M?UhANALNb@7c1n9!vj@-v9mIf011t_vzqc9`l&Zv!3-V>%Q$=*64Jw1>3S~o98^|IgxAMC-SS'
    ';j(_E^{FQXs{criz>un3!tL!H?L;sx1pZF7hV*AJb*dN>SVY2U?XTRBp{9f0W=Y8&<`?;UH`F+3d_x1HW>QRr{S#NZ+j=eHt55D0'
    'Wz9HZ1Gd7>}NuRW{U#w)9zx91786CazJHIm-9+&?Vo!q|aRj=yDy2dlt!oR#;*$vrme(P`jt?c~f2~T*!rq-Zy-jvPXl+V`d**Vt'
    '!!oJMsd}v?Xmd)<<T-'
    'P$Mz0EV8@r<K~KJ=ky<W_t0$$D>f*vssz?lFIdEp|Ta^RQp!eYD3W_F67;(LN`CYySM&TYC?g?)xH3{^BH?wXFJoyl?uS&F}afzh'
    'm?Hpa1!rFZ!Y{+C2N&&)z)kX-{*l$G_<}{ic@VQ=j_OP5C36viqB-Jmo2yPxypS@Y=TiXIp#bdF!7o-'
    ';`ftzlm&)>EO_}mS645XRfjQ(CrIe@PhW8%T{!JV@<IAuETk|AJ$~aVq5pOb*%jVZONJq*@|y+FUU-'
    '6Q1|xa+rRzWJI1jm^Bc>5+k5_GNp5R754pwX-'
    '+cCGe|8_A`l+9KT=F?CecXK7r+r$lpWAQ0T^wM)*nHM!eOA9l&d+`Bb2q=|_xzsC=X}oRh{@Uqca6@~KF!8>UbeCQi37U2DWALbs'
    'P-zK$%gFsBqf&}y&RwWSpV~ux4eZ;p03tJuL1k<>t6S|_PZ+{;+xu=+aIhwnJ*~*IT7plPVr6sPyemfS^F&O^W`U3yhQ#d_HzGIz'
    'UJnWKlzheM!)-a|L&Gk$+4f4>9A$|;(opMGq!nC@m0qIb^V))vB+}!1z+$5TQc~vFZ;5NW9z+qhwY#IlYg?;oO>p|;b+ckAU-'
    '%<to@qry`g*j;L@dS+5Glre1EN#e&6Zo=^`(_f_=eSuYGm<2mjz7+`i^DuW7lJp7C46i6^zcwOrYHkIt+7oQ?}ed~@>6-'
    '~7#<cP#6i>22xp_K*CLKeD~=zWe%7%tO|6w|vT$hoi2)*YW3l-'
    'sko2WL2?}YuUW$MK9XC_{A^w*!S|QzUr$wmLi|JwmzJ1>0<j_)=0^ATRvPr^2NO0Ih4)n7=u5{N2;|OKcxL{v0m+)9RrG8%8nfWs'
    '$cc1j_u#S_!s};*iGLpPPe}4cps%t<aAQLe8(Yw?XUf{_L;4XIhGZ(c-'
    '<QJ9`=K7d!N{!uDK_F^{@Wbmao{x|G4*Jjl5sH?%K(<WbdAITu-k(|E}-'
    ')u0Gr^2if>O_nJKylZyk&@7})o&2Qd3?|IMbdrmIF6I`P>pw46a_P4*iKSMl47x_dZcG>Iq@fG*Ie(l<|UZ-Lb*IVbbh2hla_W61'
    'w8`oFo+TUIFuFuVVhK0C(GPIW20&@Sp@B6-'
    'ftn+Mp8BB#7OSk)QZ^VN2J#9<HoO~De(VC?D4(p)y{<a(B>p9t$&bO@VJ)2sqz2{i}pYa)=aWwm~kAC!{H!vx(j{RZ}YrT=_rasS'
    'Jbj(jY$9F#DPg@Us&TZ*M#~$vJqpo#ZdgPvLe*f?P{d9NjdpDM59k_O%QSx(LEt6W`EhloLk7VtU|3SXqm-kw4_BiL_@Z1`E<tty'
    'wCfQ$GZgiB)O1_OpmHlZ<Pkd{Am7jZD_7YyO*SGrxzu*^S-'
    '#xk@*4R13CsT}aNS4R%^FHs>7{w=k;wQEZs^e%+jD2m|^EYs|y55cJ{f_VWj@C6g8BEag8HWl+7@2yl)^p2#==`F?<nOt|bGD@7I'
    '(x6UwlM)1AA3%R%C|Y@Ph4=V=gR4N{_nC!-M>D9Rg_-Zllq?9m-'
    'rj@JbN;^*pt?{fJ1DXIM@EdmhwIP51YtllCeiNl+ASbzaRb4A3a*fq-'
    'D>K#7S@g>vyx+?3GFM=o0#LCB3}p^VaWq*ux%nTsFsg*{hcoyR?3>>%pFa3FI+H@Tg#-'
    'WJZT!Xg}}+KhOsq9yp|Z;@lWt+*|%K?BzkztLxBhdyjo--'
    '+MRZSL|T7;+}#1HCF67OhEi9?uQ%O_lFOXy}$S0+CSRIvEMkvdSCjbUwWZ!dZ%}KC-}j6_`nUVZNLA*U-'
    '%3AxXgF#(bM*W{QvYCJ02Xo*CZQf52ru;7LQqv)+n9w`h&qA*>BF{kK8kR^;dkwS1j=wEOYQjr<df9PHz=|<bQ(C^Z#bN`6~R8zp'
    'wctHgx8X%HO#m{-|Et-f_nr;*D+D_r3g4$tc)a``~0}P2DJebQSI>IP>~`WbeqHavA=pVr(%6oEfH%E9y9ckMrAp+i&aVWgE}sj|'
    'RqYA%9eR=a!#Nu3}gAntcg>WbgEUH;X^=c>_;Ab@;42U-'
    'L)gLazHby_plS|Aap(KU%!ydXAs|^rtuP_S=8^Z*T61e|Q!C2v>0x{>b@Q56+)G$lf>hLvdv51YAJ8coqIA9Ma4k(eFGT$EEnAnG'
    'XpE68`8zKIB6##UGWAdoF(@eh+^Hvkrf>-'
    'ER50OB_>c{X+i8<KWynwjxKr@8gfiWX&DT{Lw}D^CkGB)>+pc+0}i#6n|9y;0}L87Z3Pe%RYE=a<X~FD_#NHx-'
    'x%MaprN|&tC6v3$dBcsl8VGgu82-IrB$1h~b~dACcMV%pbW&EB@&8JpKqDQL$3<NM!1@hd=z``}m`MoY2n+{%E!l{Ejt$6g#-'
    ')k8lzABizxWAN}a&j~tQNdHhlRG@e^~Ph-ye_@i12upGGSLH?-'
    'p|CaMd<zuzJ!?eR6O}6FA{1I%r;`hEDGQ0|ZG;Cn&_~(4i=fLPsr~RfeSjQp$$i0Ill-'
    'w8osN#TI${+DBYR|+MHGhQfD8B=*6nvb22^YE)e>B#{8UE;*&wS>Le=c&XJ!UU|WIwZy)_Jz?%%-'
    'p}_O#%JW$(`AkIMhNG=Icb^x7f*D7grS_@nZv8q34K;g25oxW|bbTAn52P1*f^uivl2AKi1$J&T{{HTLf!{)q1Z!-'
    'sRf?scyVe{>rDsIH^$NBE;!lV|uN{@^ULL;O+c#@_QM%X9dn*uLh0@I;^TDW7s&a-'
    'sXpf8afEMzEdwTR(^GulXZf03S<yGW_5j{s<;?h(9WyyY;B_9DmTh-+BDekn>{)PkN9)dh?s#-'
    '24%&7ygTLc;JBtPWJIf_zchSVB*2DVf$p(elkDEXYkvHpVYF!8_gWj%pW;$OwW4Ovs!j|l9@lMzi-JAcT|7he(9HfX~(hh%;2zi8'
    'h)j75bKb^ia&xyH!oEC^BMlA?hTBy&!N`Fx%|=hec$&r76SJrx4IvV*$-Z%{hYe~zUMQ4gsYhOBf46j+i^F$<+I?dKG!`aYq;oJ-'
    'trcEee*@(j_4g3i9zv4FL}vJ;5v9*&pU4N__CM1toflef8^eN$9H_k_T?{sdB<D)Fg(-'
    'Uci+7&zi#1==)ocWsC+nk=kXJs@PxJ__@l=><}r=ygg+|Xb#48<;g9fa;tUut`MY*8y!A2S=01`OI`c;kcETPip7B3yK=>p7vyVT'
    '5&xb$4?TPDgE%s#cuogVRsqsK-'
    '{)lbyIhWv%PG<gyE)KhRkUtu>^33ZW^g$og>(rWZKI90)!5cYG_mJ$ISG}kI=DKj17x718z!`H|^GE*9c7#9jnK{@DI_kiG;E?F<'
    't6%-<Ua#U)vLxS<d2^d=CmXrukKXlN-'
    '*xlC7ryXZ{)oN3QU1tYW8bLj?E@D#^GD?ep5c#5ms^h3_dfoJ9Ler7{E@W?dviYW6s<8jNru)M8%BQO$ojppftf#&XNv!*{Y0#Lk'
    'Uy%mc_Dwa4=cS4e*`O&!-GF!gD&Ea%3q`_ZJXBo5j-Lo)K&Q-'
    'dPzsEHP6Ez!8F1ju}fqY{;1CR_@h7iqdh;mS(x*K$sg6ebZqamXW3`Sko|!Jh-I&rKO*m7rT(w{uQU7+oq`d-'
    's_Gn$%3u9i%^&ea=@y%Qz5EgG{YLns`uSPQAC+&h_*H{HI=vbEkv&JOSN_cZ&mUdDAK9;S_}$)ph(EF?&HT~8M-'
    'TExWoIwsk5Yd$u(F-'
    '{Bfc`75EEM)?l(K+nt!J7NBpTAzVp2LBll#@AMtB&MzzOX$RCx@d4@mY8>Rk8UL2o5ykt*vpPV;YSwFDQ)E|XEvexpRpAP=$vh_#'
    'fzVGlyxR3JZ8pFqV*jEO=vzI?AeLGZt)UV^x_;O+{`AuXguQ2?PJVy3<u0JAA`Z}<_o5~-'
    'pxTDj{)E~|F<pTbw^Bc*E%*f8cx0&R3hCh1fLm#^6q!{S3{1F^E{E>Sd{wVR79ANRj>l4$77q7SeXvG=r@JG?7wVc-VM>onJUAF$'
    'HWGMIT%KVYFtnLU`j6WhXv4yybU*~uBsn$))aH_$&A^vEV*H!tWih&laFYyJQ<3{R_VD}aCY}5_C_j|whh5S+3*pAi9K6ied`lH&'
    'XminWYz3gRlyzwgd=g$QGsBAmCxr3EH;R#PTiXS-hM|1s=*ALVmU4}n8@4adxU|&1@QSC#`AHDNCzq7T{*KFNa9Q&a1N2xzzf9;X'
    '`_@nYy7S1F5k$Nph>W>_ksXr<ocf<E7T|JjS8u{A`Zh_}p^G9m+9`&e4HGjkw-irDo`p<3zL%xVVif?v^Kl*|%_<}{2rDMx_qnnq'
    'lKY~Hlezdb+cs#@(!Et<F+1VZb=vLJqjic+2@I~s69{>2qH->@t_}GvA*u}5o*9>m%LjI`q@O0G4?C?j=de*aM{PR-'
    'vM|6e%!S=E%Y&9E``lI{rzyBbA^q9vy1`gYM<NW#j!20aH^)fSmG`RLl^GC4x+i$;J4b4U#i@MwLKf31ViBEjuMm-YQs!#f)Px_?'
    'hk1EEykUxSG=RSCC<kVkSe*`;(anJmbxMjqh&ZYUI+T*q*kJd4{MrCj4_zr(01`#Xq!TB`&agU?cdhhv1Zj%qbbBy?Ahd+Wv;g8^'
    '<c#qHg%+KuSa)iqsHMXxV1Xt((p8f1+cl{ClEI({HSAJvs>htQ4?z!il)}z|5+`pOsy|Dg>KZm2(#~<O1_$_#ief$wToV^m~^EaI'
    '%JaqUt`()O()BlsZ7!y}eKIc+%1Otn#_VGvljuU}TiUDA&Fl6u3=fR$bR|<FJaUXv)WV^#3@l{6t@!t9){*3d)t9oDAn}hrj>=$m'
    'H+9R0y%pc(>a75vc;GE){SHJqziyXzN{6zjSJlj3M<G_?te?*sY7UU5*;r#d2ABinW9*vp1moV$pAHk~~I289C9_zm1kF3AcAK{P'
    'Y`lEgPQLVcj{z&X{9)F~^YF&SXgIx0%=hYus*TDq5?!DoU{QW%sNG^+ewdRjpzdbqiM`Yr6TnkKL=8vpbpHugwxjdi6)(_tLQv6X'
    '}>rLa2QbXqT(xG$fkH`*&W8FGGarBx$3I;XvNA5k{rMEaChtH-PGk@gpeSRkw_c;8KJY70z{aW{BE6?yp*5R$>kKC6-'
    '{83%!x%?5m#p%!q9AkK)%kW2RzBNp@tVibpf0Hi}{zwfMnUSH_aCP`2cvQF}xPbMAKeBh%Yd<ag5uc9_#y7YMf21bTwUQYboyQ;f'
    'J$V+6fxEQL8f&%na?Kxk&X$+o)%=kFHMo>~fS-;05xZV{(s8Ys&N-G_!C%6|jre3Qe-vyg2YVR&CpMGpFUudXPe0rEqc8vRFF%A~'
    'z$+I1Xy%OA`k6bL`J-T?^wFAUE7?znz2@g4f3zo$ZmvJ-7~?$tX!!DC|1<oNI$HZf*}bLq=qmitLm&Fkg+IDky7pl5M|hU-'
    'M|3GQ^CL!BaQbi{7x72g$Ng{c`uacdeeWete)5yMN0>cC9V@%&^$+~O4}`b(`^9fR{^LL1{$|B6!4OZy5ByYkK0n8PUA|}gc6^HR'
    ')zV*PC*F7eVZ(4@I9si!)A(h>7M;p%v;O?<JFK~>cE#WOZ~ousI)|AzB16}lT!VpWHz(i_8|~{~H}gl?!^PX9S61^J?43QByx<S`'
    'A-'
    'Pf>$&vi{2<0cYtem@R<+GJfz2yJG2I?G6gC~WfAWQqc+&DavIwbX_;yZDZIEs9&4Laf+qZ1Cl=f1N~9#a?MZ~Q#}XT8}o_#(JK_r'
    'X1N-&}JJ^-g5&F^AvnF>6k5-nael=wrx-'
    '*?icCeb^>^8owoSBSUiYJDJkQ+E>Ihrvr03op7m+AL{xZ8<`C`w!V$m9=nb|VQS8eUCz3SPIx{26DMqqKC~{U7T<M}Bi#_|skKvs'
    '?vZad<k0t%9O-ZlzXyw-'
    'j+tkpk959e>(Mz|tFVJwmo3BesKc+}b>{=u@$n!3@hwAG{Re!&2Xy@>y}Re0d)E6;bD9%|OCFtf{~qu09-'
    'H#f8s`z~;nQYpOYbIYi_G?6t86&GtYRy%d;6|p6LA8*tIoasTk#g(S=?KGTI&kCLT_O1m*A34vX=c%^p+lzo%m92Y5AD!DqP|Cm;'
    'dr#eq8ZW$ESK^I8IJZ`Z2tvwOz8*zX`_T+;2Olmg9KfgLHC{L0x-'
    'l{^$QYuDz+h?|t6qeGXxNd*hXgb&k~0IG^%&^<?uIiOIwYeci#X;O(Pcq;Wy}?Y>@ibZ%bb;qmD_es%C1biU;RBNxl#i1cRg1DE%'
    'j+J3!9T%R9*hY8gBK02qb+L?F)m!Td27hk%8$2cCf9fx?N^Wu|h$!%q8>ZdW3vghR4xW2Uum#S+#ooq@U7h%x$CTlhO7(a&%h9i?'
    'De+O<U{(xD!Z)8_G*av^gk2)hic|FJAB$^Y^|7z`5UqKE>mxznIrvSfR+&l3H%e@)#HapC2_VcGa<teQ%GnRT;Zf+m8NsgmV;B?d'
    'twCyijlG=)vjdS!!p7bwz=<s^QBjUZTL#lgy^pJ-<<VYMfaUuuhQ19_QZF^yf>^%G~{Zsg;>>12M9=lw~7rp339goTBt9@>-'
    '9!>}Q**%Z+laa^3ma%ig-&pYbi})ir3_R8zWltGc@_altTutfU(YwCuySA*Nf8-aQGBR|IWJU+rG5SY-hcEzm&6j-1m-'
    'JrYx>j{HmpSawjUVFgQ_twT@t4nd#xwLESZbo`eE3P715kTj@3HjF`m={$fj?@#=%YXSqx(=lgZrS<qt2)I=V4pL+Rb&n-'
    '}}AaQWKcoF7yh{a*4QO>9KRyU3abXHM(~q{TScb^+N0n8xtGtcRq0Z%D24bEqxB9-'
    '}ut*_e5558T?*0dCpa*+g*R~>}Nka>uWg<^*ptg%=}UPzQZ5s1*X2pYw{-'
    'WN90MycoBFDUW=|dH@q&H(Vbd9?H7Fi_kVxnH{&s$_u*Rj#BBDOj~TLPdn*Uc`k@Qtw)SE93X$F5DCuzPIscOHP`=!<UTfX7pIG{'
    '3FKVoX|6TF@x%|<dUTn+$vg%*g{gl@H(Pw<dXLRihzNlo}doZ5gTC6qFaa#Fp+uEnMqu<nyy(xRnH(Y90>l*dkS<VAL9{*IF!iJ2'
    'vs$-{-2fN6PP7eR7W%o5-^EEBI@|BvmQ-3|av-'
    '7*lXAMROpKF{L|G`%hhloAwz3E?vKiX3p*J}_?=)G(mpRxAq=7vW7LCY!iN92WXqnlo<_rO@&o{N3Uzv#WI{tlb%I;67chx)-'
    'DCC8%Hl^P}AfwNiGj<tag5WC@_>fW8;bi^8o@kamJ)=#|+@B@18I*+npEo&S>+4HWEy6?XG{I2$_`62oSJH{WRRsmna{=-'
    'YiW$;JslZaWxDsr3PD?WqoL;f()`mE-R9OOk0$x9Bw;Ey`)wEw}U@j+^-%Fg41Iu>EW>XH39-e=>il{&BfyeB{T$-'
    'Rc?z3an2@&EVK$aTz|9MUQ8p|8g^+b_u$_u+axCm%5_z9*Qw$6zJ&8GjRg!{6z9;^tt>!9wT$b!+~}f%k!5tBrwUxexIT!XNP$9I'
    'lgoCtmk?{A_EM4`24YeP_B*K1BC=ghSd-abC_@e2JrwXZ9`M@-6P07z3x?c~_-'
    '#&3Dc*UFl`l!pKRrzp=&md~p#OCSE5Om_nUr>zC)`td<P_m^v%mxjHvIhBfQ`!QF$^&DcrmkJ#(<2J?P;ieFZPlY?yte?+D*5Z{e'
    '!Nq@U>4sCyP4zPX)tb^W&OU3TaE$2rsJSU6tC3fOqadX*+j+t?ndLYOrflH`089m|K9@ko&eYvhzgkR!u#AbL?e5vO+Qyg?S;neD'
    '-N2TkLbAwxtT&?NoZ}f5Ik0Nsi{lXdHk8ry3WAoW~XT5AZsz1s(kg4Z5C48>e9AxhQ()W&>{V$t>6XpL#$4mc?R=)C)xEjwp@-'
    'LfH(HqZmIfVSB!Dr@w#S)$0>zdt9b|5vTu2WqbeM*m*^rg%}f4xT6@EPGaV5rGi_q*4_Ek&;3n4;%C%j;tvMfad#KZlRqw#WO~1L'
    'qdL&wBH_&lvY)IsEQ#bl&&kijxOZw(#0TF~|im?I!qa`j^1t!rRPw?lTse>n4xj!F&L6l7kt{&~@9};_rFRXK@Yof4)@mRFbRB55'
    'bj}zTqa1rv8MTi#X#*Y#&>i9!{AX5qa;!mG~C57LTq&UeVKa&v!9-=Q+E-tNQVi!CSN*<*>&O-'
    '>uK7)}(#2@i#fL`X>bwDm&A5D{I=m!Uy0hj67;~qVvAl9W@7XP+&u22Ev*BwETO#c%REU=gc|R>-'
    '<)^C!GT+4!BCs$t!T^XU@$v*ShcAD|xz(efQFNmY&*&F2XGMMV(*8zmszYkF7NyznV|hhZsx`3x2MAMET1TcYo-'
    '7k1vUzoYAA3A;Sq<Ig}%vbJRme?}g6g9r@|!<y9X|y;3`$&z`Rbggm~F`?!y5p2og&8UDz@ZlsU+t>TaPnKOSR-'
    'q^<<Swq2w`PJ9KAD!F)e{^zH{>b}B&6IfQrt(LyqM1JuTgYLtkMr@)<B!4v9paB%&ze6Xj|Y=K8hs4;QJW9{@DIOb{L!dCxsX2^F'
    '~_0{YyK!P-pn7(94tBVwP*gwI=of<k>1$+){>8Nx#j#(#o7yh^t7iv?Yj6Qxom6xsPwh*R=&l9#UGWA*=tBG>-'
    'F$QwIAIOe>8HocJ{36<d2Sjy7(jd?3yZmZT-'
    '3me`No@9{%Vd4|&L~;*XqT$3$h9V68XIA6cg}e<b!8wY9zO*%SVG*~*_2{Lz?+BTtas>gRBw(f8%1^GDYF@D=&lH^d+DGq1uQ)#o'
    '-AY41(%l=Jwb7ryX?SK^Oq&9yzkABmC8Qn@03bh_q`=-(dx==4_eM{vaON3LsCS92-'
    ';NKNSITYDjY1kcAG*{h!Nl&AFiBaiFhkL13pJxcu%{;2G2c%56uA61NaE`P+X_<sJcgAXzBN9_Y=e=i^IQvA`|-'
    '~RU0*umArzSqqk)xNUuM`}CpN8&x4kvN4MJvaO4BL3*bFMe_R1$BNm%pZ*$tX@BC_(lBD*L~gB<$f&uks9EA{E^z*TC<HgoY%kZD'
    '*TbYfB2*I{3AW<uF4<P-g6cH=;TKEqlyv3y>;I}7!Mz(e1*OI5lj;1Hshg*LBb!c>yOUkkMyr&qa&x(YLVB-WxtR=QjbvbhPU1n{'
    'z#APo53I9eAfICIj#947{9+?hChN+pT{4i{>XaP=LkLyqZZrak6!-'
    'rmzz7&v538n{pI7AAHSDBvR3Llo4;UFNB_UBcT<}LZ@iWK5kGe17B2niZzg|)55NP61KkIh{XGB3<ESrb{>XO++qGAlt>-'
    '(`d5b~9A6XOlBli&gopVql$=~M}*S%W!qw;I7%pcK#ef$yJKDfHrEgXcHO+0ur`6FCV4jd9$hST6%sXw}iKXRVokL-zu_#^MVmHZ'
    'Jt^ugwja7Wgs9v2SZm)U9f9&&T<e6RDk9{woxeGWQ)Gx;O>yylOr=bOPFSzj}MlsSPjkCJ`Icd!YgpHTlldjnevKeCTM%DJ-'
    '1YyQaj=ktB{=$rGiia(nB6tF9<Va*@epW!Y15P8CD{s@*-'
    'dr3H&9sbDqxIeHkc+PqJQR&}#{LzK6?G^Z=lbgjKsUgmqCf7s!ku~D~ugD+m9PVTJZ9S8%)_unjKNI;Q{?BFkql%;3H{lD*@iF)C'
    '|5g6TUavpbRrsS(2he$G_WmpKM_n&H`swP;K=&G}4{i@@X6s@1xFgTihuY`k$64!T8~o4GgTy|aUPt~eR)C}MMb#m}SVoQY$>`JH'
    '2i;-o*qhXEvmN$)dq8^9d2QIVrS~R#mD+E=d#?UJ>pk2_I3&+wLsP?=T%<$&>-'
    'akSAO45`WgE+nQ(NABTHzb&e#3K+SB}Af2#;ItqbFVZ0@`;su<WcO*X|nA?>II|PmQu^@TiW9_$~Zxeo5-'
    '}`E~I3)W=)1<2truZqs)7#@&}=^xEiJYjK?TSnagWlauDX$#){}?8p0hf~9}mKK>{?*4Qh3&(gz%?v-zRlpbr3d)(uW_-'
    '_0Rvr%wM^*UU-ah0jx&DNg#K_B!%*9KO#V~@)AZ<Cib@$&1QFfCWyynT-'
    'B(^KcrekCuF%*jul44H}#<)+#v<>j~!{4M^gdteRvYzN((``Ee9^m;z#K7a9ltP$8k$*Zro_LgngVztuUj|nEKCs^rXANnMcWAw4'
    ')2{+n~`QLoty|!7rF>yoQ-'
    '#KkC<k&6uLhhj+25SGUg}1%!ZLq@R1Z?=6VgVe{=%2kQziPvefcwcmtiNw6KJeb|IYwrqmwU%v{4)EEd&EyBGn_4*WGfubb$w+15'
    'q)*NV|F~hpnWX))nxGLpZ@8shvnzC{3=H1{%Y!{JyzU6FONRrBR)dUH8^0$T(w?ry9^d6HghdQSM|D^dn%m4rsbO0=PtQdcMrXXJ'
    'mevIrC9gD^0##_S|8O|h0h~L{&4c0*hV_#V2kHto*6af-|_WYcB8-'
    '0wrpj`wq#_V4&E##a1DGEToO5wE8O0Dog;f#@42dPqF3879jkq0L!avT(cs+9yccGA5r2X|s(aM7Mf_R5R_;afo#K9WbN0nDM`A6'
    'r`AFZo%nqzQt!4L;m%L<IS8P-'
    '1cz+)sC%x2ig!3TF@N(og`u8>7Zx$5(=nB0du3gd3KAQW#@xAJM&(xo%{)qokcC_y?Zaeu2k)J)m+8wjv4<3`f&1|Udl{fcwB*R+'
    'c*TSQb8QqKg$SwR)^pPA(XM3J#YSC-'
    '`T(+l1`g6my8>1XO!*NM%`zm%bqpLYiIoba9(wDyU`1#L&e$Ui>(vzNa(RXZXz4p8x7_eB_-T{-'
    '+8wfUik?y7bh~1G_Qu|=%8`XKN_p+Al9e3Q(-_8F_Pek&<QTkyU$?-kk^F4z-'
    'x9*kBUQ^SrX8w?UvR?IpvbUBl*vrq`TlXD(j%Byn_a9u<4u5p#op-kWjaoA6>bTCeYja1B5&dMc2kf<XIqWU?BR+?m0l8UpPi}#_'
    'GuJZgXYYIA-|WBS7rs|d$@F#+4-Ed{QZ^k<C2yGRo#bF%R`ZK_jo&bOi7vh8V|Vx!qsQXrb+3Ef!ZqUtotN`-'
    '4{OhBTVDQcX8rO5k4v`~A9@|*tz@;HU&Vit*N~oI4)>|&Sc)gilX}|Ip4PDj-'
    '=yN0w&84xYb49?N9F74zkvhU*9WHWxdWaDC*x<X&v#$|-BSn_<y=R<(ldQp(+e=Zmfkee+TT`;qDSS?w8vPl-'
    'ABZpVZX5M#$2qOW43wr-'
    'hKK$?AmepCw-{<W;bw1a)jt5Zcfe%`-7V+yVLQ<lb`(L=F)JiwO4eHDZVK^E&q4jt7=pJLF<Fx<z|$Rx3kZQrR-nwg7jn(C&A0a3'
    '+xi?Y0Oz|*$v*ZuYt{}bLgBdKH{i@qXYVIZC>`WmxX&FtDd6+7k17SV|EOZ-d=oYG21@B+_{K##5{O=cx%Nn$JVSoTL-'
    '+vAzzie28Y!0!yC!{<Fh{ZxzA0%*khOk9-1FppLyY)fG^QEiQd2Rm9L!FLdPNeUYJLHK5lKvJ0`!_rNo6^GjA(?h}bN-'
    '!+2NNblum^rPE(XJ``+N{6=Ot3HNL8M;#Z!E6I><TMyzD|AVXX9(b1j^I6Vy?p;S_xFh`$`M&nLQCHi&!W??p;m>N%>;6q@^zpfG'
    'e)F4;R=sn>D~b(zzRE{_<VSYzW_r(G#zpb(;IQl1%lqI1>({Mq9GmOr_m+I@&3#R{Bzb+-g1kGA;x;jG>0-'
    ';*Yi4DN>HJQ&=`{Qzc)gg+KH~G~bZURn?>&4|{ob=WE0z)Cbj&{HFm*iSoak%nkHkjg&L4DMwZHUvx)$|EcnZFib?^Uc4Q^qK`pC'
    '&$alWn}?}wAC`_j6DKdP9eF#>VaT4wcKWW8WM6)Scww`=oxWMe&AgI@C}zNKe$3m1`EAlHc>vld;Gn9uvIWqvenYvzy0Sw5`4xi|'
    'ivnLl)R=8p6vd(CTJ(?{m_;4vJ&+kw*<GhzGxou_m5{d_0aQg&)P_@kvCpYQeFdbBU?@JD)(;gs!B;Xm|J!zr0_BVU-'
    'Vvk|qXcmCJBRlW51Y`7!q%%eCBhlHz{Yk$JyWTsQDiClvxuo?6(b0%C18M;Q-L-wxS`px>ZE`6`hqdTtId-'
    '<pQ)H<Jz9Wz%7&xAjk&nJKLoa_fS)aOO!es}NdymoT=;J0!I;W+YF;o;W1eT{74VsL*x=ffWMu;u^C2k84`jW}nY9qu){Wvx5hKR'
    'RUn<Td(4CS;RY66p`dcVj=szScgI_{4foFB!TIGm?8@9qKo#FE#rhuC_*pe_$qAf46g*dsAj@XLcBw&qwsrnxFhg7|OZ+p*ZZooS'
    '3DDr#;%au@7_~Z(zMS!XdF`>D?DjDKiu7=k_GN4&T{l*k{RwFA&VYJ|EmR*zM?X2bby@fA%bEX!Jne*#oSR;K>u#)VA1u=R8vLb'
    '--WRj((f=p7_Vt-'
    'M4O<x3fLapS<@@@oRV^`ZWJOe3WhJ*hU?{8G*HbvKwtbMlMqKbFQ@n3u`;dUz{+v#(?x>7HhfZVlnZLxOHF5z^~ww?URu_eK{%ez'
    '~vWw)@Oazas0kp)Q@gCFTOsTVO}0T=z>^}f4wPtBKErI{MuKDAEyto{T??f9uwOnPfl!+ygs;S#Xjf8UvjAi)_HW3WN}p;ymnds$'
    'R6)}aS(drUlKd)&+|Xx3o!+pou46BvV7tlzGyyRVI$W^jL`gt|FuW*A@W&x5cZwzhdr0<mtNZNv(d}3d#MMHk39}<CjR6T@Gto=_'
    'I~(>_sp}J!((SoPxvFBx8{$MJCHgDF$<rK-Sd6+2zZO!!sMv=d*)v{W)A)ke{@K80}td2_WhDup=O4>%pfEy`6_sj)XsRU_jVpJI'
    'q^%ABV6Z9_B%C)qkjElsy}Kw&HnRA^+T3ZSNFN+_So<FrhJ2Sk7w7Gnaj>UIR~!SHL*F7iM8i<@h{&+tW9om3X|`YoUKDMkPh)j^'
    '6Fw6E7s3k_Qnq23Vc|)MwSlGy~a;-sKc*4V(zKF8Tp}$-'
    'B)X|=7;EqbN09|x7ohLSFzvQ_wjps;*%X4CofU`k@xb6$&PP_dvgzxlY<kK2Q&I<XI@9^?`jUxnfjyb<?dVR0|zeKI7Y3j#)V*e_'
    '7y!&`C{RZU|)34y0)IZUhfU=bhKw4%EBLg!Y6#fHZ#|A)P1(Eww;1C)VgoKlYeGj-B0|)Pi(A-'
    'DZgZWv@cz82kgN9*)gkpeg3B&%;q)mTlvcF2maFBak_6^(@i-'
    'pYK$^FCUa0yi!_dw9UV`vpSs6Oet$5(^oO;Vk|F*GZ{!G8Pi~{G%f3&?U^Ta00hf0Vvahv|IObFA#ah`BzSbT;VecL)SEKfw9sa2'
    'H&F+OR&V^-UUIBkkjt05Ob;)d`)Pzh&eD0Qg$vXYxmbF(lec|0;%WzYBbg*aj3uH*94tsa~z0bMy>uAi8zaE~0-'
    'M}|)M$PBJTn+x$fw?SmFL>+2J%?HFi5r8n#>64!p_kq*y>s}L@`f*%^V2raTDHf+^@iRpGsVhgFSQ)-'
    '($skD<B<GhepI+4zVf3U^{8v3Zsw}K$d%>pJk_W;r$;{Wk!SusYAtZbeE)01ckJBhinkVftM8%pdeMxU*+$pCvKiRsvKN+)^1B!N'
    '!cPo;6s{=zk;gp89o1gk=bc`|SLmU=<HO1Msaw<70$)Imm^up2argGM(RZrzSYg2BBV6<yopX#w);HUJZr>Ke!5yvNOU#%$8MEwR'
    'IP87nwgcB(?~$EX;F`oXbFEQiCU)^Wz30WRc%yx~w?|f;0}ZE=gHZnJA&%&x1IF8&ReGeWvycy5aYNUVjaroEsmdO~YC9j*K5L(v'
    '^87EXKPnsCvzyEJ=sdvs{G}I=SkDX@drbBc^>@~BYA`(ye`M_(=<R(7i*DY^UZ@6SaLulnE!oMtcZfTacg1%U$MTb>oEiRH^GD8$'
    'tk_0tX7~iIrPplz4L;Q|#Q5&LHAr(EA=^0DhTxB${`9AJ4hhUzeGCr7IvM_P*CVMvg147W(67!zzysp8237*EmUm#!JlH$kn&WS)'
    '5fl55URXPNj#FUcZ@>Na{#~50_FwaSa3M?G*JpqBXD_;3{%WroersNP<};t!`?|bxxE!Bcp8meMT#?zK`A6x=In^Jv-GDz-jEp1d'
    'S{k`yVgMNb9e3Q(xoh%>tO55{t{)5rb_9<pU*NVC4%InX_HT3D>N9roZ2186hcBA?t*lqF3wJroE(hOi@N<c0*&^4`d&G-'
    'g^rGgM%6Dm<D}O4pV;W<9#VcOXaics){5QYP9&%{@k=||cy6x3`#@b_+`Xl^M>W|2byvUV&)gO5c){0xgbCyo_IjY0JYq^(ic*7e'
    'mT(h+{`+VoV26V`pEMK~PYPC9Qx8)r>*YIzdd%$-UukvrL$rrxxg)JYkqk9Q!RNqs32tDiCZ*@HIX1FGd72cdWk<l0MB(sh9^y-'
    'h;3|J`sDD?*3m!3-'
    'Hdv~3iBOH>sb^6y?&vGW@N~qhync<W?_qy|=tGHkM(clf&{xUn$v4Ht1@+3+>y4KJ<){$embDv92%}3im@QG|59UZb-?4dk`%si-'
    'T>Au9HS48I$q(&%MvFGf7?{uU;%UoBKn3=A5?tS<ev7OhGYn3<~=frlWUl@#iuGMglG8ZXa60QXfEuI{Cv(20G1#rX3TX&DycGu1'
    ')uuk}?umL(i*Ywga8{4%wt6HtSGi&P_I`2iTjJ*xcLO;Z_eit9Z<9%1=@?=I49fA)|{L#|uZk{<sUg3{&kR$)leW7=**Z;xS!yOI'
    '&Xs3Uj@AK&J8g9dRc(3#F|9l_v@cr%&jNW~5UDic-'
    '2;4(vh>7h+9lgA)t{u=DrF5>>?Z6QD5na1Q_vyNNTD9eRQ@Br~KS#&5&fOZr!N@rk1AFvZI2y;g{>YJ8NNRo93o^>Q^1;Ei483mc'
    '#ty<U<e#WN@`$hU{gDrS^Vw{zzd5JW8#xyoQs$TC{NUWFM{-'
    'T{*Wvv9ZnkX2pgVCI+>3nRJa7p3nA$|XmFIk7GeOx6@#Hj%NBv^+F{#}nOV8;Ry^7x08|YV_!xtT7;@*4BdtoqhZ<*BFWcE>J5sa'
    'Qa!O}YaZS<k(94LD!PBmD+zF>4H`Py{KbG?AF4%p*S8`gS9*XX+Q9P`B52NQdiy*hWF;p@Oy?A!MFkt4Z&Z?EBCp>!nImKj9BJ^d'
    'be<n`D{vVv8GBeAEYf1m454Nms3_yPVeektCz);>NRm%XDOa$L-&oBNlgpXgkF<h#W*2lBe{eCc6+Gh*H2+Rql-'
    '=zBBwDfnmb=Hz$#J@s7v4%170npl+__yOdUx(WUfdGgl>SJyHd+-'
    'A?p<ul8RN_;7H9l7#nFcCHSbo>x*X(kY^Q>}s?v)1G^N8x7jM{NVmlAmYHU8c{(@b4nG_P@%8wH(x8i4kCAd<$_{YAD$u`@MTKKB'
    'I9x7>QUSd6BRIcwX6-bMYmy-k7I)v+J|2i-W5*-?>NXgVnc}|J*g-'
    ';*IPr**oMZ@Wn<R)VVcWav}J~a;NyhYVFy6drj(&_&3RyEW6trk-P~wC0suEa_T%__Q^+a&&t-HW*xCN^qw#Gg<trEJDdl-'
    '4}V~t@Nw+R_C?sHyf8S(z~=Y*G3-'
    'Ou7JiF8f!BG=^L_TC)*t`oID5I;Kl_?o1pb2j6}9zVv&Zs@QoC%eTes}r$USJAU_bHPdDI$Dj~v)j_lh8|@I&D{@J0@D^f!KA>Fb'
    'iuH_iJ^4gqd<M-HRbuzi(q?(!e_Lvr-'
    'g>(zQ{T*Lk5w>j65b8zN>v+<kcQ>gVQU%}dIu2J6wbpiWymR{*qpbpyJ&F_`}G5XxL&2z8q(e`tgYH(9_cJOy_?1ewzBj7pIA*eA'
    'j&j2p((3^(8My@c1!6)I7yWT6<`#kF`^HoQ@cTlh9=j6nW)*kO(-'
    '3<F6cXRLS?47(@`Ho^#d3AJ9%rLI$bj~{*Jx_vjZASbU>{*P~m=rudbse~lVD%$kTJ2Wqx7g0E5gvTWrD|sI5oR3m*X(Q4y6c=Zd'
    'Z_kDeot~h?BV8umYu#8wzY8)Ji8yblRR)W;$tR!AMy-KS9^YUo!_-'
    'lixV05=fKW_&8JTjeAMsoUbR7FiciAFz3=<JZ?Dtxn{TA1x9b(e;mO4q>tgW@%{zJKGoQJsm`q-'
    '<T)XCmF32@nj(M)%b?^thhAQ4q--'
    '@NTOt9P1r{pZ`^rlOF2RWK|Dj)Cm+i!0^Y1Dco7fl_)rRE5pht&+9hn{W9_gwb_JCm!$*XDOU{NWGJ=lAQl7oTOWq<R`PJaZk&CG'
    '$aWp=Yp;vfaIAGbcq{kaM5;j5SvzCgAU=b7LRFYfke+yN>JK-tFC%b3IRH2VU><NG*x)8+qb;`>Kt8NL~N!y{S*};~bsO;IuB~o5'
    'S(MuVeQ38GDTnmiMO5UtX)<mvePEm$|NpPNwe2qkN;BXV&?Le8`9NeHNq6b0*jK`jYFW&tqVtt>>4mony1<U#%B8@fX(r<8;E~=&'
    'f0Pzg|?$3-MDDhlqLQd*~$<TMhq_n^!*e!j;o8YjdvAa;W{FYvh!*vhSGZb6%EjW4rZWU|;zi@t1H1{2ACStP+L=f0tJPixR)f^-'
    'Rra_%6NToOAgMi(cvTH1o6Sm8ROcYhyMSo3`}I9)4@%D0)B0;}|{9nln<<?{U<OwO;XGA~OeBrZ0kZbifz5bbY0@X+IjhEW6gE_M'
    'Xn!Ex&ym4C|a)t+ns7Q^!?0(w~n<8aP?!>XmNo<rZC6@><IuX#HE|>6|&rZxvfK-YW<Cb3gZUyI-li2zo{bBRlJL^yJ*Te;u&Jo!'
    'jg>_}F~#_~CSnUb(06l9B7xd}FQs<ZZP+C4P6n2;z6I=NXTf)MxhIqc)3dKKYYBdB%2@H92}aJa+Osx{oak_Wt|tKQER(Nl#8(t9'
    '6l@7<_bnZ}XH{x9;J{A6jYvFWA5Of8Y`7bL0++nbZ)|b-w<ndE3z+{V8gF;@{GXbSGELG3Ss4M;f_yr-N^6KDK-'
    'Sd@6Z}hphJ{uSa|+pPU^dE4oT{pY~~=)>w^Rjca-Fo8fcfI(bL1*0O~iKj4jAqrSN?OMDqzfDdT@XP3kxV=p{+ZN_h8htrpm&sK8'
    'Vu6xFajpz=2T61q>7C|3k&qMMX{U>4H3s0#&A6EI@-~HWPi-Mog3!&nw&f~-(u$wT<*T4St&3Ee^njRE%nLjTE@?P~DxFhj-'
    '#mFr~IKTP@^=&v{`Msqd)^PT#?8AKJ%>xfSaIW7gf8zPie}1ofSf}`fA1|lMIr{85rvTPQF7yXhAl}gXM$MHtR8OH%|FYC-rS=l$'
    'kX}gmeKi;L{^S_Z^#vdGKcikKH9-'
    'A0by+wPI_NXqORvMi(pL%Q3!e@r;`7p*WAr@e+9SR`j!X>*jK1z&uUF?%^6i+cem^rWTwI^H3ihg(8JkcsWcM0)-'
    't(T<_fqfeyYIfcePMY!WHMoKEz8kMpkoiUNEM4V)=B@^y^&|I=qQ=1HGm_@S0Upc{J|e&Ut3P_6u1tI9A}dmNPIf@xz}+SaC_^S?'
    '!h(v9{wo&hu>id-h%@e{84`fZYrEq-HXN}$@1QN@9o-D_1U!s&eZ%&Yq9ZCwOs5ByEE$Kdwt*&M_pv!Z&)Q;p-'
    '0T9dpon2?x~AEo#NtNOK?3Li~H^Vr}ta<Eo;r+$k&m&o?w6;Q|FWaAqSi@z9BqEc+T`vOiwh}g7vE|5zfe_;|1-'
    '9&TDX$*7G7ed69gr#P@3E<t?oGA#Loj@)vMY?h$+IdvSC8sQQeyk?-;@?*i}cUIeL^-'
    '`DqrZ;Ef`V~LOP{ro@}iFFOP!nLFhX<S?D$;=<&al;p-pPlbb-$c*pU^wGBuQ_!`BgZ#9OJ5uOBYYd3fx-'
    'E1wx!PFJiq<68Jp5`0)}F}vAaGO$2odn_B`NOk8$d7S@>)Dft{-h>m9XZT|WYY)DzyLStFnS`JaD0-P5))<qs`f3|$F-'
    '6y7LvLC9d9F%f$=&;3X~b9&)8!kM#q{GPd%J3T^uXJqX8$nAlNpSy2t>u2_L`4XcyXn%&!a}9jW+S7M(W9<F>CpE|RF?l!gi};3o'
    '9oRPg=F^m2=|}G`{ob*|WixusyT)}drCDAc=OZ!;2ba3k<lZMwY3)Cy_JZ$_dqj3*$yRzC^1HULrdQ4YOnbIhzCSet>3QXQ!WWJ@'
    '4nES(J+N1c{pE9sL18<v?ehN{ujPA>p5goMp_nth$Cn-nj`Uti&!yCG`8~Qba_X1=am=+|{C1D_Dvx>1ckyl1IpLhyO}R6puWj?u'
    'c-`{-I~Fm2i%nc(=j21y?1nrXcE)4&HMYQWHdBs5$&#ObGx5%ox&Fa@i++%U>y0ewi@$j-'
    '^)@+DcggPLe$xZ`5FPZM)EuU+K~0OCH8O%Hi$C<}@u+W5YKyER>&k2VI9S-'
    '=hn7BX9&r$5@4WY9_A{JwYJQ^k_7S;6_5u3=er)iNhw@)KXQuYmV|j|!a@oow*mv2-'
    'Yp^o4tzseAkGxk{U+_M!?dfaLc36z$bLC9QEuZ-'
    '(=T5Ha7cZWq&(>SXxaCA%a?|k)4$p@iTYixt8I#{vebraB{<3lG&4_vWUg__}2e0ee$(eFa=~p-OWBD7sw3kd=XzwNRHSDqQA-'
    '*0wTF$7P7&Yv2ef8sY|KX=_joR0*>2)M-BG1U}0-Ut-aO_Ru2)SrxKKO1vylV{4H|K`KPx<WntFtxE0Y9Yf$m`@tW|6UbEjJVg<Q'
    '^m!EWPsR{OD)c+>$z#VJCNViLcL2kN$<Hd+?;&_8d2jJKht!FY|HSL$%yETe(VdZ{P!W-'
    'gzgkApHe$zKv7CkzwC39FOGaAVafb$dK&dxa#0wXs(|x#3#2lr<&N7gPtXHV2ba=HD~-gIW}xCKNi<Iuh-IXdU>?+m2SJDY;L3ub'
    'g7L`&rR47UP+#$-YEDCJP@wUk4O2<@LRlP-G|mq`3Pj|N1q&iDIHw(XcfaH_kEwAcy07_-wb@{WNqJS-'
    '85$pLs36yKN~UPrec6&+-jXmaG>kbP3sx<%SNv2DlQ@O`98M%=2<e1)De+2Kf-&`?+>0;@rHg6-'
    '4_H`T{?cWM@|=g|4xpyJYv55hzmV-PWsw+f+OmU@MT~2Wgd@kZ!?#v4oTfIKF)Ld3fu@k=-lZFy(rssEp-;_nL;Z$-'
    'nNfVGM}LKke1DSG*MNL@KSh|T<q{0;)nWM`q1@t)Vka&vn$jZ?OT@%?xPpT-FM#|?&r2ORwn01UnI7_?DCNsDzmoie{gh{gQH=m$'
    '|m)GVvni6T^cWkg$}#ey%whZ`HcL+7tuesvl>h15<W9EMfq%Y(Rp39PW%eID|^!WqP|jmmX!~_@BTIR2*ZVEyB=~aSugJ?IUcm9&'
    'W#OHTR-wrHm`cstFArb5s&b=9rdp;g{59CN4Vb9SbELcCfkWax;Ev2Hoxkctd-'
    'OnT@N?yeCY~XkvVeqHu)9e5;d)3zCgz;X0yPD<leza`EPoyeCxM<s~T7SB<#D-nH{fdxouC*R_dz4dxcB9Hfn|VPHGX-tETZW`MY'
    'qC$SXZL$*OeyTG_a3=>wO3r!Z)H^r&IIwx>StqFSx_9ydPg`{a4?6U4#rZ|m0nW*)Yl7qAsRI=_2QkB@!6_EJ;x;upWT^`Q35_6h'
    'A7;=%ekS<Q)rzb*Y`#$&&a{4(bTR*}9abv_Hnk-nQa@O^T@<<c+f*!#%So=nzk41J$^+wA-'
    'Q)?s`kUEm9;#lcg{Cs*54pG{V$=W%SwPjkT7#W&)y#A%Mvx25Z+)v35fvGu6oY2Bi`_5J(4EA=)VU&C=n?RM{La{l;iqrdaa8S?|'
    'L&3Pm@Qd{aC(^ENa^2qQy>?pFK{PpgQHf9^b_8KQBeT1JaxO8N)t~=Uyj2?K4FNFK%gC>80jUhieU@sWlb?5o1uYl#M-'
    'H%_Ko_FTCB*)M9$Q^=ZlA&62@?&F4emk7*0sD2^p}l~-'
    '_&4x8n3I_X&v?c&+IM8P)K<btM~~Ybe6)PL%u|BhE^%}4x5Rvhjxl>RITX#o@=@XFweHx)=6~hOdR}|tqF-'
    'g#8VAKGz)#G;dfVIHrUtR+<-!g4py@+K|Lh$D!*97A$OT*PPpJv-HH)ifPhiikT`n8k89rx^6bHgYYu{@wXqp4ocvtwKT=&44n-'
    '>b-'
    '8;*C)_2x+L_soDBb@}1^;N!_t)g!6<%a)&stKggWEJ|~_<{2S+|KKppw)MTvDHv%mM2`bMxVDNF&d3X23mdT>*oLylZG(qj#P8zY'
    '$a!ghfnBt3s$-jHq>ugp3m2K*FJuLaaEQ^xf$8PqeX(itk##-t7yJKU{N+=(9k4gkH8aEPm8q-'
    '3CzXtwSI`%u>|=AA^bT$fV}rfZFR^@Z(eOtz4}i<5b$r`Cd{liYK1od_Zb6>i*M9BS_8RaWzQl8%``o^#Z+OES+BWlL`K#=Vxu$Y'
    '3V1L10(#y<x7(D~}z|-Pv(tqB)b}g9=6`ALNPmGz)J=YmWqizY0gZq%X&1co;(mBeJ30EZk&s-'
    'uh)fdi@IyKMLuaFhFWqwrnBUs45H~YJ4O)prHo|4wM8Zzsh|D?9b+-'
    'dzp$W*PR?`ALRp7efTu15K_$<=S(veriDkf_PRe>$J!^?1ylNf!Khyo>rKoEjY0xqDCWUyoCL+{xg}J9gBUSS%^_!zIF-'
    '@aFo8ss$Up<Qn5m{gEU31Oo|&<o8iWw{RtE{wVi%@N>N`9b`go>D@?=(_hs=PaIw^yVCXWa_eDWBOaiGef_XH`4Koo+#oy7?yxDt'
    '4_NvSr7x`Wa?r8lybPJoInnk>xjLOcF?upCc>}4ZWS^#fKns_Y*XN!$GY2x)BwfTG1-'
    's6Csq_S%Yo0QPJv=C^51%{ssm8CxmG(__2l3B*R(P1vLtY<}@E!K&t~aD(=@Xoqe23@hy=Ol(H-'
    'QhNuUy#$Yh}3)*{7X%c%aBFc?9!J_nXWgbq`kg*<{1Fp?lUbe+X9^J}I@FsgI?z!*2AoWTs5+nYB6P;%!StU7s`cAn*7~Z#eaf_;'
    'vS2-5q>cpCEPa@qNYO@H2k5*zWO<e|+D^xvqrnCO<3uQC^$*qqz_A%sE|=KT=;Uuej^Z@#kzF?r8Lo%{<Aro3Rh+Bb6FO-'
    '|rrbo?Ph*9Bz5D>U-'
    '01ju=;bxXK~ye21wYUhkt~P<xYo)&2xKS@X_i>z3Y#7x71~f98+UmvhY@g?}Yy?}=_k_rf2+RMSf>J?OkP`j0QQN8%v%E%AYK2){'
    'cpc>9~rIGt+qdwz9hgR6-jbM4)SZTTB*|JgJ5>YREtxJUOwP0bE}Q#?NM7<PPl_?lSK5&kGWXb$B&%jvH@x-'
    'r}P?z^w$IiCldc<^A|o5R{FSvMXHzn~{-'
    'Imk|J%y_OhNBXxnk6E$SX?Q7qQhLzq9i<m0&cJNqk&`~pR_%G}&dWKZhEL9neA&@UDSa8c)=b?Rzrvou=cUi;7UYe<PuWD=5q|{^'
    '0VCxH(CtS&;t?&onLoOy9uek<$8ycSU;hWaCiy<%I6ArNIn+GIzyUh`Qd`8v$fF$dYrEb92O>AQ^fA}ndo6uVUqLy1bY=9t>;435'
    'T_Sh3*_ui3!r&irmTm=SbP-3g&Y5LL;959G`k-'
    'g0I<I=(xw>+MM&G#RI@o2hgH?%z#jN_)m+#jxEX<rty{~L}`>%3i@R)1}of<t^7u=}g@}n`c(wf_@aylD3u~&%&%+;NHDEfc7&?C'
    ';dZrR+dnj|?AaE~z`tJf@Sp5CP&oyYJ4WN5yFoJ8?1yviC8o7Gy7tC{|iXE<(HS^3OI^Q@VfH>fyat&`nTLVsztP~Up7#OTe@+>x'
    'Gu<zII{$4m4#x)k=PW*1J!c4i;D4%wgKkMgLeP{kkgxBZ7;r^5$XYL?|ZmL48mgwY(Btt_XuYbHk>c-'
    'NT9OOO*V&0Fo7W;RJ(rM?~T9r9FbGJkGnD2gNH)Y!NAKEa7colkSJaK4K;hC{VIV}8lezMnDQqiba4UGpLM4)k#N51ogt|5NQVw_'
    'U_>T;ZO&=Ju(?bNnH(nAuUQy|eQLV2bL-YyZ|;qI0y!Ro)xEBRp7YeDH2~DEdc^b589!d-Hl8Y-185$8)D=Uw+aj5x(-'
    '&r#`jw@yXA7R<pEverfH6SK^PZvOcVNu{r;R{?*!cP8Zf8!ANI4<eQnnHh8zo<ihv5#$o6^2CI0-'
    'JKhmYy0MkIw+rXy@SKeJRCJJCBscbO@HoA;S3NU3C)64)eQoT2u6es+eQxjZnV-'
    'x~^8?^w`Zw!CXC2RTP0fPCM|+=I7P(03UhR<;19b0N*TAn(2Qu?s2WAZ)je5hDf%RX%cbr!K+A@1ePICFeOPyf!Fuf1?P+|e{vTp'
    '4w*{8GTjQosw4YW-'
    '@j|Z908D=Q=lz(Z>@fYxGWM|f?nk~My+J143Se&1fUcF+Ai~1Is*Q35^<P+}P_wsqy`(N*UIX`u5W1dsyDJ*MPeqZfz3nxh?qbKa'
    'b%g=|;N$<(Xk3F%6llcXGP8Zw|*QO_q7=qu<x6%WI%t}X2_HbzD)lV(hLuy6Dx@sc_9^E}D`M7MLIM7e_Lfquwt8zSc?wLE)lQga'
    'qpSkwa=1p(~si&l4YItuFf0P+^oy&p`!A*LuwowjT?XNJd?oEytr-x5@%2O6yfJdi4Vsaz-'
    '|1+1g?rAsXBBd6W?%^wTdXMrY=#@Qj=vLz+Vqe(blvkIYJ>C08oHb^v_6+6GcdX@SUDCUGKHF9OAm=1!nO@a?)B7N~v0?O1jSt*P'
    '95l@phe0$44vVR^zvzOsInOCu&n;W?N@ByovB107$o7NeBUvM(-'
    '&W^Um;QHN)ieXV`?<js;UME4^xt5d=@A0URul2YH@>lPmGAxD?`@xW^c%jE&xX4d>y5s;&4J^O<PatwT&){>ZI0a2pZ@f|e-'
    'nSy>kdXVaYtRZQ%Co#hC7f)4%ox|`}~^NM{G0t4tI~tq5trPrC*19*9RVWpmQ3WQ~B&my^@~&?$_w=q=!4)sJUNw4gK^t*pryw^M'
    'RM{%Qc&ODZpVmZ*a__Z5}@NPMk0H=Zli3wINpy_E76{$A;l^GgEiy&FPFW%z3KhB9<mcSi_-X(z({VipP)U8tPh8%|XD-aV)qA^*'
    'egtSc7Fd8&@jbU$9=d+vs=JacTMj!ueAt0>|^bbakK1+BU&Z)mp>ieJ7uP%#`mLkLEXtJ?i{AKb{`)6YQyaAegoFUElRxbG>`pmc'
    'd&#j#by+@p$=lOU+7VY~wujv$hwI6|5nT^cH>@4oQyIv!DI!#xL<la97-9+4aUx)E1?GBtD`1-'
    '*5n3L!?Gij=TTYuab_DTjn2yKf;svo4o^HT*tC5@wE6S7%&{#JxI?#wZZzx;$(cs=yRI+0{GIlqXUC#JhODZKNpsjUdp4dZRR_lj'
    '^3x;%T-RN@A%Bm{LJpbM?cA!jt-ur`>4-'
    '&91N#y692FHH$D#gDh9vv&O3X)ulr!Vx%Tizj?`*+j!Q^QlHc7&vbzj_1cMsfV8@|@FG@eW%=hZ=mbZmdf|J7C$;q02{_~%|#0nL'
    'Q^!lv#!h8Cjs2i0FJ!-UeddCI_9GqXD|B!7TC8wSBU287)wtM9{ztXRTXM{Tp{zq)RV8-'
    'cP7d|9C*}{F~NYA$5N*D1*hic@#H~j>|=LK(epT?Yv?WpzEvul~d=`rsgbu;+4_F3i7iGOfY`(`EKQP#YhIu(1V`9!sM>1n%D2Rr'
    'wxv-auE=!MyT3nm}_Xy%mW9)OYGCHW(J7k%kNjyc~pdc^))^U>qvFyub^P8|M=U;N^e(c_~rz3?@w9GA|QU?<1ysH4$4viE2BE)L'
    'SU`G4H*Ti^QDUW3j_3^g!}<`~R$(qC<w6|&?v#D|`9j|N9{$`6T5lXK+t%)ntY^zLF`*$sP`$IPzCYy6wRAI-'
    '5;*G$Usx%b|Cd;PjU*=uk}^pVZ5P9jI=K*s)VZyIaeewW!%JAH1%lzzx$s`tn|^5gUjpJyw0Exl93kLw(h^6A{`p2soxo|b|A+w~'
    '^brexXvQG9@*LycqF%gHyjdk*>-pVNJym(e}%-^U+?I}$5+9p;KdQpZr&Z0}n5BX(lVA3gr@kDsynbNM6lH7~;-'
    ')jG!?w_lmwdAFKBTF=3`1b@_i8`+WD=>6CI9LScBtbY8Sd+u3yjPzn0vzh4mP2rF9B7;@I0Oe%J)4&~7%x+F6Uf~dbbab=$BRQ~o'
    'hhLFDY8{jhEJoEAzx=c2Ki2$_IfZ=8^Z27zz3Nrx@<;31qn}Cqk!ytqiOs_w(b4nxBlw><9)Bd?vE<&lLFolFaIMCS_^s-'
    'tXa0yk8(Cb2KN1(nJvhW4U6t#&h5S+Xvx6JqkF3{2{1G|AO5f|f-'
    'm7PqssCVO(%(#cQaYX9ENA#5wSekr_F#ZZPyh4yqu9g2A7#E}$3Hm0pUM1@=QDqF|NZxO4=KI_TMcU%@!83kgWSCb^xL?eUVpW(p'
    '5c#RPICJ2M{_+U496PM(^oGKzM%Mjh2h?G{^-'
    '2(zYKp=>!@+F<lU=33V&4V70z<A_@ngjYW_&>8$U?Da{SQ>cgIOwnm;1LTge{<yWhtj@fmQK@LT6I__u{Ws(8-z-'
    'E#g2mrwu1g64W%mOs+Rhc56TVDmSLKROA26uu}mTj%jdo*&|m?z-!)uDw>XcQg1SIXLz#K0#*5mMoe-'
    '8ht!2#UGg;=70ER`q=Ezvvc_)dV@a_`&X>J@JDa}{84%#X8za>@JEezUoU^emz((`{h;tiaFy^!snzB?@t4G1D}U^a?_F_7W0G`M'
    '-Rpec>;9bKk8qqbe`FTg=-Jl#7Wu)5@JES@qHl2geO%BX{>Z-UXU)Z3hCiZTH^?8IhCj+2sWpF8^2kidUeC^--FFS@b-'
    'wdEzw<)=sNUarNa~Z!vf)pcAGh>3P3_jr;*Z?7i})jPHU3ENWqLTx-0ImmbI-rz7hl95iFv~xndLlk<bz2s{E>Y+{1LtOJur;X53'
    'pkk`wU%!A&L`VM*IzZDF?>Wvg1S3yLpehUjB%T!XNQLF2f)BJG^-'
    '2kNDFgzVF9zoUESj@JE9KIhQ|TAH;lYZT6?9KJ}^1AK``6T#UXKN28Z#-#>i0SW=BZ_@nRnp6_XUHhMQ-'
    'i9d2a`}m{LS7hOj^vAvgf7H49Vr#fi_@jv<I>;Z5*<9g4VDSroq>o+tUgM8o)nZYYnO<$9ZngO%n9P`yO!qftx7D@u|HGTctf0o1'
    'ZiGM5GvP-0qhM|O_#^gATpaA?BK~O7<({24^G9Y%;XA~M>Rn(y=4#-'
    'NV087rXZR!B1dc*%?>xon)+!tsUPAAJ>6IUNQ~4u%efXo=Th8!D1E*{}i;Y*mBpz487i=~)2l$yf&&Kf%@kfzc_#=H6#V+BG%(J-'
    'j&O5u-$R3VEGRs5n82dV2=_3AUu0O&*&_8Qj{ze_kx>T>`|8abBWv+)m8hm~8BIYoT`tF%OYP(K$)+k-'
    'WAJskB$agWX?e^PmZ|=>Sgay+>`zo6^&qDXV))ZTZClXhyfxuJN>wNm-S`%$M?49bv;JX*`NA{5G<&VTmd-$W1L;Ml@U`<!-'
    'bcR1tGlxHNAJ}kQ?7II;_#<oEcc~@uJ)^hxGDC5N+oWGi*P`v?kKnpxo9rDw<M|`C&*Y}(6`VZ1yz>5$AGPpD6+?6#oxf-'
    'P$(~srJN!x6LHSSOCVOeePji2&@JFuAwbP$5o8!9pqs+-Whd(;K8T`?hCAg12Iz7Z6!9-'
    '^Mh>q$#L~jN*z3@jB_cor3|B(Bq4*LLq)H<A*taFd(T<-z?==5gsM`c4c&g-'
    ')LQPzTM=2wP4Vtd&ESo<OVh|ihWe)jXl`6E|ydEI-wH+f>>$Q6IIkza;CiY~7CBQhOx$NIYML-'
    '8Z8gFiZ*`6Ir^)OW3WXv0_WH2P)oHRa-'
    '$om}ebog*3gF6YM&z{{q##+ppM*xa|y|MK6<59>La`mM6tnIU#gPxhWeBNpSI!^g=I$Fa}%5(mIA=Hs0Hb@Ck>+qv()`}9@n`f7G'
    '+t`&8Tj?91?eS^E#+L$BLwRw83$x#x|lb^p=j3>un>7C}Y>0$cfiIe1VjlFosc4bW`ULaHQRZ}l_8n*{SQEws^HXFd4Liq?{0-'
    'udzf|J$$0@LlD24?BP`ONoq&&@NCM+TpQO^M<0NAv9Pi})irj?dJK9gl>=f??>RB9DSSW19!|x9~^!D_Fp&;qr+4YCR-RK5_kh(F'
    'ML)dNi_+qgE{bYxgFe=3*>+ZF&TH|CGzpdu91A*KQ?mbj2QRjd@vv<f$(!UeP=&_}B|x@Pf`2lp8Geb(q0pUBKJau+$ps=W5K!xN'
    'KAVVB~c7-FLUWOZ~88<k_)%-'
    'T&3x4YTLi(e=9Y{@BkkGp+wuP5Uap|5nK6%2)^vOdLP@M>T!~kEQqFj$k_CTKMJY*WTC+*}_iM<=1|AI{J;Y?5yQUmzTL4`gl!sE'
    'xoS!#p_s&|57sSz7FiE&-'
    '3}EkFfaeCn*=(8oX#7UiE+v=~KyudW2iXK3)YkNzXbm99Tm4I>39tqG9&<7Jf&?<e6)?^a$shl@HrFcbCN=N}sz|-'
    'KuwB_cr4bi4|+@T-'
    'VGpdp8Um4hI9apJ#RnY&bQ3aD=jN)?N2jI<&W3G#hE%d(HO<yv<@KH{b0i`F*fM`X?u<*4x27@SN}7*H5pp8hpL}7`O#^N%;@*dX'
    'Lw$THQ;S6r61It!tYv&QV`e@lf|f&D^l~OC#^T`vUr1--bQ)AeTAX29~eA@J7M!$qUaBt}n9nK79%2IxBmpTA=l8fkXD^f_r(UUr'
    '*VLo~>bigLsxL$LF&-bFTY7y%@d!I`;^sVK1zhV8-y*T-dpv2M<xNU;c5+PcCcuy^HK3zi>$KXy=(;lz9*RT+Lc*>|PHe^`<vqw-'
    '-(Xw+}zm=fJ*3e^R^QXI%@onor+YHZF;7@^9&y*h($#s&C@K9<_AbJs5n3n5W~Y@=LNmvo#C%7Ww(npUk@S8R7+di^E=G4e)n-'
    '?m8D>ZQn1l9iykC9<_aKu901WW9$7yj(8D0@%go8*_-'
    '+Ks#m?L`x?vj9=yb%8A;7$;O5MP*)v0~u~a=i$fo?urQaBApY0sKyC>~uectDN-'
    'nEHCYP**Dt>hr=(`)O6e$kKcO+%jginhJJXieb-NBu?jGRSOhv%2jmFhw}b)F19r2Ru7|ZF**m{^-pY^E1Q-><peEa}?pLs~&)-'
    'qj%fU)PJ|-'
    'XSUDCx#&Jyr7Jy00_MrirUx(kO2;q3LGHv$hx$qKAxBTdmeuGB&421xLY@%6z3#`3A0$Rm%fPQB4>5jvi6zH1JxbCeBXLgTAWuLa'
    'Bz~<pnx4d#j~tb@Wv_Y7Yx*9*Mkb!&cwk1YYkG=|IXI1fnp^WjKlDTG_t@w8Kzz1&rrT9HBs%XNke7K1@Fp`m@ZtIi=)GO~pIpiI'
    '75VwDsrIJiv$fpj9&6_viSIoQ-qQc$^Ly@1-M7U?x}V8q#oe$^<XUT|<8bFiPVacfI})q5d@FWsx$#rs$@n99(c9kkw(IuuM-Sy*'
    '_hMwZDDqFtZ!@!-PH88t2E)uAy?EC1q4ZEN+tT}L?K`Lbd$6auf8D-'
    'gmhq@t>wZ#$ckCH%;%N0AIA(U6+~~g^d)D!IZ~OORAs8JDvFt$iA2G8@4Db73^W>a)^ZM6aa!>4B9ln+RgURb~BzCc{;KaQTj#IX'
    '+dt}eEc+vwueSR|IjVwnDz0=2O?#X%R@czLe!Oxd{7++p;at^q!_RZD)mF{#7U+q`yZ0}oSExz|zuvhOh!{+5Le|ev$I3JEoKVfv'
    'EhaHS^ue|im)0Y%ZZjaNeq`oV@Q}Y}pukN=eHnvZZCEt<nQ2My^<{LG*3+|I%r5=NK!imHp&fni)z-'
    '&!=E3JF~<rq9|`||j;*S_|(o!9IBju~|Htote9;nZ@G3oHj;idQt(3@&D_nVDR;I=%bU5vCR*{1MsV3-'
    'pV_Rn>PUR{*}C*Fo=pqX$)UaJVga5#53dz?jU|vF^mVd@Fm9wZN9h)g1cQJ$|Ei_5pfEPU2ig-'
    'RtgKr$3+T$7hV*gnf_6h>S<=S3kFxSWlUMUgz65wjOq7E#YVCdT}z{ThDx)G1sWq9&DE!V7}_Cyx%pe-'
    'SM57kCa|+`{o~wK5BjbW<t;}ef-HE&pzfKb<MTk)6Xvb>&Bd}o>O6d#K^Hpy=QZ*a5MD~cieGDYGoRev{%|&9db0RD|zqUZyp-'
    '{5H^wCy5vRHBUWCpFm}qh$tO1t!nFsNWS`82cAw2Urt4l?^B(JdYg1p&Wly(eV9_&wl)pL8)F5Q$l1E244+q(&Kd8S&4t1pWyqvP'
    'uH`fdI^gf(k>2J$be|s33b+4}`{?v8RBk~Dnk>00%pZd2g^9AIl;nl(w=lY#b=0rKy^hS-XPtUqF2N(V*htJA9jx~2QAKCxIOZm>'
    'sJaZ4}Xy(X~MP|vRmv5bS_rhRb*a~Zu9UFaw7ax|7Vg?2NN3Z&^FL!?=F%~;yj||t4drU9g2mH1i2YY7StM-'
    'A$Ea;Q;IS#)O`<lHcd{oXU{n_UEN12Zl`<gti^suuAJolKMnDhLjxi2XDky&?q9Cjiz_rg7glXH-'
    '{&vs7ao%wxi4I6FFj<_(nk$y(5(o%y2GsmmR6{e%5oALoV=SQrQo^~VtZ69RhO?8bd9@u$AUcq$d>!0|e*7f+=k$G~r*8Gv@Gk-M'
    'qP8@q%<EXf!T7O-$Qfs4U2i|wzeTy&V{`em@lg^J>pPlDY@%>J}IzEZ>RZkO6i@w^k+!OnQwKHnum-'
    '?F2Tc&?;?zQ`Djhn5+uF7*hXQtXtEG{kz_IeI~)Ody18tw=~D}TA??}aCtb92IhS|=rw-Ydli<#)(;X&e-'
    'n`GOa`V43snn(U3WkDZQrO0Jnt(0X7-!JG>u1|s9pk23$$_LKjhSEF+@XGkrkTwA#)bbW=XF8NvZSuwNuH|FAs1NGD!z2Z8a<v-'
    'Es#8Sy6zGP4S_IGd{b#C^?UJtNjT(fhu2I<eJbFs%YKZIW!GqsvGQKwZgeK2-'
    'hDj%u!ko?&}&r3JRzGYZzOuf;W{LqQNZ0<F4X?@0sBRb!PUr}~LytTv+a3ky6{9AdKd?+%6rO21#=aCm#!7oy;b%Pv9+Z(nPz9F7'
    '+;F84be2VfFIv=UdxqG9i-'
    '<D@pcBEqsd|SzJi4RI|<RiHLr8g^^G5Cwt3D>DdP+b>Y*^#5Yh20o)5xY*3zcl(UcMehcT*s@t^c&)kZnS^@YPNjixO{VSNW}GgZ'
    'gmM`PIs@7Z~yjh@1CyiYu!iJ*776gdf(|BZ_=y8oVDjSRwwqbPs$6dy>(r0-'
    'tVP*d@bvpO*6Cm!Qd?q*huHwwNmyZ`FZKhdLWkFi*wg~?;M|3zVemLao8VW17#0R#x?gWb$eI*%=A&V_u-J_2Z%+?AF*%x9Oq}gD'
    'n5VoF+P+FF2+B;Q9a2%@4NZ*_UthOdZ)$!w$2Y=x6F_$|ERe$d>{O2oyUC9ylvRg-2a0uW>-'
    'e7Nb8L?YfrR?r!TENK7F^vLi!HtvBLi_*N`n9a}^ezNS=Y3!6DDRGk*2ZkXNv0?q%N}_X(~qUl=|HE5je*NZ_SxD0#@wO|FOQ$!w'
    'z3V+?$r&AIM-Hs(yTKm7aH&c+%?|4ba%Nou=;@3Mt-QT!)<6x(@T`wDEmIl?_XDEILeU3ZQ*Wp~va%hxRbspn#se#0>ux0fr)m$r'
    'Y{_sEAoh_@c|!5aHdjimW3$sLE`k2#9Ty|>@A&RvDClq=)=eWv{$7Aw~pzf|k8@2&L*({z7E-a6c~<ARZo-MHO3cHz3$pFP*TV~h'
    'CBbTB^nRX&FucWq;aQRf}mPgfksnhV=|u#LDHG3v-E>id8TaBlD?-'
    '{<q;VSdldGBO@>7p%#~FsAukUEg{^?cKT8sU|1AS=EW?*Qf?w&9NL1Sep2RKjFC^66T{@vwT;3m3$L6R(~pM0WQKu!=GRK+SeYBn'
    'zX*=(vwS{o3)u)TGoHbtNZQOI)isD`v(lvceoaILk>}F1-'
    'm<P!gq4@<T2{kb`{;H$8bwF(|%RHbl0Kc+{9+qF#ogSvhEcu?@6A5+AXqyx$zstL?bRZxkRl}+eb&m;rlqP#?7X=Kiw-'
    'Z*Xp`+{d^L=hu9Q2az4l3$SXZ2ljBJD9Q)=;%}4UY_T?4SeQAsUM_78xhi@Lq5BtRDVLQaue4?S-'
    '=hn2rwo(frmS<CvcRGCh_KoCemtAc96gEBhqSh<=!Y1MtMvtEL_ijdfwHzgf##1uCr1sQ({UiJHGfPx#L?`W6=hTYq$jy3Fm!Ni6'
    'J%Jisw%*=J2i5cA#q6DRpI~?khbRUnA2J~$@y?WA+quEyGmbM{(%_KVCo(Hl?%+#b`qKVxcFA6ox_ca4?0eaOw(l^I@@JRNfYIf='
    '@4WNQ-'
    'b2NiaFU80&gIznQgqk4&N{cRm|?Z<{qH;Y&~m)ss(csvB_~%N2471*rEz`c#CP0MpO;vBsoRp5ocfrHj@hSA??ipcV6nCC>GyJe;'
    'Te)+k-'
    '2Sbo4OZ!B>neU@FlfK*1wu7HTSun;;4Z;UYFgsC(=>!!hMTnVq^Gy@Cf$W+7)}VFLV9Y=$Y1gg!?*rdh|iBMsD$?4*B2W=)r~1xg'
    '9$#UNt|*41~e?HvTo@gSJz21h<dJ#08JuF3H{Rx=`zuTw$Wg39q$vo?q7SgIY;E5kHh3TGQ;~=rz%`ljLUKgoUZO6uZ6t^{+pf>s'
    '>M%iVr?s50~G0@HjNO3ELr)kr&@beviE7LmW8p5cNJgc`){G_%7^Bysdr(9t+pE*ZVt60Jmvvk$3I$OU;LU+zc~0@nlJ6YLE0SbK'
    'Vu-9;*|x-@z^Qy<lt2q0+~Wj*fWXX!HVKa<AYHY^8f>ox+yk6251)_5AGcY-'
    '1+JzWEgGlgp2n*UJWaUt|}XN51*pV>mu*s`kakBg_gir;L9+u-'
    'BgV4Bt(>8SGh~J2SY<v(c~3|A{4PuRk6ART?u+4N2zl_^j|6k+u61p3clA|0kX(-'
    'QTH=Q>(@%lzm%fyM{kfFJ)#EACo*%%ai&PcDZCJPn!Juy_v&8#_spmfBo0X4L%(_aQA!iNOsXrYjxyL(>d4NJq<H^$Y-'
    '$;_+7RH9_;U4_kH1yta}&|S*U+-FYF(0dCOb6=U{TR=e}#<R>OnfGaSL=!yVxs#2D6Z#g*HsfA4mxn@g=m$9XtoIb-'
    '_!sv!{{yB_;hW?iu(a(4C1(3hDFC_AWjM{Y!a|BRJ~10%b^lebR$T<4^(liA?xR=6^H=KtW2dS}%dRVUTBS?Yi0Ie5Y62QJid^ZG'
    'viXnxKA(ZL+4k7Fal$I;{1u6k|{?RfbWuXx4L*n^Ko4o<GEf0q+l_N9Af;zh*;_)xewTubepSpe+2+ChC_*pzT6-'
    's3#vsk`STzwUztx0e5(9#CuoJz}HCGyaalK19DpO=mw({ZZ<(=J`kQ9aCqtul^`Abw>Ts3C<CwuI5o}!e_!CspYel9b;A+d|BN~`'
    'yXHY#b2DfxQ>;`c+^tb15>}f$oEN4dJ>&n=DgwROOKnY8oe2suUB6x=fa`h8#j#iw0HTw@;}=CWQNh`9o6eCv&7U0x#sksWlzVfx'
    'nBF3b7kL3{ZT$6^?{Cg-qE}!=DIKX?C*7NdhO{W89gPJF{kV_`$+Be>7CX5cQCE+%HdDv+6KSV<$11H-j^fiJkL~3-'
    '6L7e^D~`GeGXiG@#${_bGA3C>z5yFKPer7hjmOXFT(lFwMede)?>ey4dl<d*9+gA8b<f7?wh}Lzm?jrms-nF$FyTZ=Kc<`6`2V~h'
    'OxPW!&+n)o<Fne$Ze|aQU`sE6S~2kJm>nhu21eT?zPrf`)6=Q_0MdFb(&nKfxY*+)xOtt<9aD%=49*wS;F<;wEPtuN$sDlQ~4aWC'
    '3{t3smL;~h5O6<!ms*1_h7!qbKZg2bu}mDy5)A2d`7uEd|G+_uqk^vd{GUpxucnH%bv*v8W>jFGFW|T|1(#%^riD4#lvD;In?(0b'
    '$(j(F1c#!wHa=j{8Q`g?`F@qPvv{-wFi$mx-6G=3we^ZyZBNvl-me5gBg|2oqX5sdk#mfHN5DPYjd5colO4-'
    'SR9N_e!TegtH1iIck(I7Ew#$gEBAx`C06yhqu+)1cfH*$;)oiH#R(;rhi9fIn|MAy;z@n<#1C>MYadL_V()Eybcg49Z_5X8J>?^H'
    'PyJEf-1RYH!0bO{L2t;g<j^%Az8n6-f8)pLpFkG#+T#z~PxT-ms{=FM<u~4l>>8)WIf%jJ@QWqYdWez4ym~i@KSym)^B<|Za-'
    '@gQm=n2?ql?p#YsN3ogMiG&eB6%D^d}J4lMDH&OL2eng_Hjn*~QlsJIcrYwr~5kt_v5lv8y-'
    '**tj3ukba@K5Pr{y+j`!!ya@Rrau3`?@lN@gaMMfoJA|ddkk!?~5aB%d5Itw$uyWL`dw++G!N%zq*^%$S@|T)}$Snt*gca3V-'
    '6oeZxsne&@Id#MHNOw;TkF`lrAI;6*W1U<7_4*YHJ2QeJvLp9Zub|mKd}pBDCT5eVF<7(J>mIqVi~<q#HRK%^#teCay6brkHq+OU'
    'dQ@C`#(N;-'
    'Gjy}<e9J`aDVzHF9Gl8a87EY*eqB&j7p42_wbhFl)hh)qr>agAPz>JJNb!a>7v{l^W1PpbN@biVh*c0((*^~3D0@Xb6R%RHoe1z!'
    'Kv&W7w|aC%uj1dJ_7!??nl?W$YX_F&iImEGkQaO!#8{b91!N)v!Y;bm*IBKIgjS^$jq!RwoUGwe3Rho;V4q0Muu>?QH$BUlk3)t3'
    'N}CQCuC7N-f@8ZlUj3a7x*T%4#j8PQ^xhEQ9OikB?b;Q&Ih7{_*>`6rob-exwRkqp&z=PW);r0uWAI;nDH@}oa#|`*XNx)z+rReK'
    '2~!0n==t>&-FL8hNAa9)2@7y)UbA)mHR#Vik(;YLbg4VGkLhRuDdo$?-{vlgA<V>+IWRMnBS7V{dz*k|Kwlbb?CPIAGrgA8*KZ-'
    'Z`Y%*bi1)iKB>K$t!9Vl<Xv~&)p(p<8)btVlYvRwlW^MPM1Sy9&QV|MTE|_VDYtUWWls-'
    '|y}c8XCne7e$5MN0`l?+?m)(E;i0vJ)4>ckK+uNl7zqqv4Y~y<AAvDj~Ui-FuJ$v-'
    'T_cX3mc4)1qotHM(n3I!v6>Jtha`evb9&ETt`;6X4`~W`BzM8GMZw#Nwx$v7(pOiY~daY~6)&JGG9v!Nm)sqU&WX<88^p+}LrfYj'
    'rD<{?$ufqt$t9moQr_0v#-'
    '}MSBy|m`rhUx($exie!M>OgN*7v(H^6)JB)X^=o1L0Kkvi6qlO)O6_J=$RX<i(el4}D0NQr8v?HZ>6GYrj6o&I}&)JbF9vJ4!BR`'
    't8Z9s%ze6kCa<C?#s@#-'
    'Fxr7_=whp(z7K8_pNVzYv)VU{;;lfZ6CljmrXyEr^2SpHg%p?yUu^?^{=*^9UA@h<$Ii@r^hUxaFKJ4?V&oP`R|UA$Jx3*p35a(d'
    'OE6=vX3~#5akawe#BNKFL|!}fa?ug+B~$rY>7$L8Tw3iNiFtyb3RMIT9-z?%u<I9uQ}AW1!kvaOznypGw|`ukJj&L-'
    'RC5AM|0iQy54B6p9yB?pmT%A?S66kuE`104^X`i-'
    'i9xeUiI>iyoP_48ycL1pPyOpo~PDh@Ntbv!VKV<rGFjE$iY&BdO;7<+a`=+?giHOhArUdjhP@Y;f)?+>Os`Q)ZgG2?I-fP%O-'
    '^j>3cupp6la~%<{YI9=V=fQ#$(w{J9~gjz{<}a*mRBH0EivuL_q9u1`i{hwvThY}f(u2tDLezv)eHx=M{|zNh^QzP>&?>YVMDd}e'
    'ue_FA}t+OhN~Pya`;OW8hHD*iXIW9v?IDD?v2S|?n1k#Sy29bLGP@*8LFu=jp`DE}mVZ$~~w`&|C+7<RksmDppw0b$AMotByx`yg'
    '3{KPuUtS*tib@y^s2qPfvAgR>9o-'
    '8$worPiM>FNaq>H@lX3Fu?)cQ=F2x&HZy;iEn1z%Nh=67rD)^=NP?WTZikKx;9pxx0p+;qxK9Y%m)&;u{Y%lw;g6r<izQBR5rPNd'
    '>o`6IrvvT9sVsiXmF2U%XCAojQ8^u{65!8+8-'
    '(=S?8zq{Y)RP^tXU%z+U;Tcn!FL7<<%$EcHsM1%zLzakMtv$IQQ&`^cpRXkXn=Fl%*Zazt<gV)@k9r8aKPF_McV#wl6NnC!tL^HS'
    'Wy;J<5Jcwkq{9HwBJ&fj_~``L9uFshQVJeK4Tw!V!X7x2Xmdw?HOyU53tFQrF;x&(T__Z>aK`|mIz_YH@n7l_`P>Ua3{{44xXYDL'
    '4{@f)lm2iwGl=F68oZBB*#qSvENeA&O*f`R`pJx#MWrQRqt$FmLbdg^I|DbF=X@Jja3fy?1v+b=!BTGA8L`uG02zdhe2z2U`9{6x'
    '8C<e;b8SA4}+biexa6)an#hOpyDv7xxa{!8!uU)j?3Tlw$mpzPIT>v8PcVw1if_;GO&`xERxwR3dNV{ls6@0{sSY$^T7{JG%X(Jw'
    'Lzce&<HQ@a$tYL+`+XY^(38bDZG>h3&_T#L?gfXmFi+?>Dl7cR&i@4CVr<sAHd=B?8Ya?K&_<C3Plsx$tl8CB(@UK@GFH-xduJ>('
    'nk@7YANnP6^m@6`8YHe398=aZRKqpykmr)?Ge%$~>Zm6vZ1!M*7<8eiSLObue}YU(^Ao2-'
    '*zZ_^{V<sLgXAE_TCXa3fhg%+DM`|OvV_i#l%q~}h^1*kZ_YiHzBi#PQ{t36%}y3DSlW9De`haUd$hqpXZ??146Hl}l4#Hw{P2bJ'
    '2S*>=*G=yh~1v+R6c;)>Xy?92YgJ#$~DxOTy(>;KQ>x;{up=MKXc^{Bzi;W;bT(5tiaB?ivdHB#kEx9sdabc)?$7vR%kaF`KHM12'
    '?kZr-o_A9=_F7;^_ZrYD=s1@t<(iHYJ@CFjQ9lAA7WfeD&fhF7>ut<lZkiR_E3o}x<~8BCTO`M>lLMpyD^Y@pUj|6loYOD_U8Ds`'
    'YE_UpY?U4XbzZeQ7l^ln(>$fv*+h!e@l-'
    '!qdjTpU?i18_9^0bi!<Ze|nS6j{LW<h75PBAMy5!yAb`#@vK{kA5B2lIv9;$p?Y0$=Ajw@yW8c!teBc9(AFeA1!~7zd&Z;-pG*-'
    '(Lo%Y7{mADNyHv-wXvSpbIRJ6;mezqG4Qgz`ONmGy1&=0GkkftygFQaJ3W!pDGwZ`EO%HREIwEI=gf0=2JW2P(C!~fR<J6$E%C$n'
    'Dd}&ZUMN_UK4Q3|iqX^-_L`+5)|fb%U#8DM#kDOvd8hPHKMApAY6{o``bSp5-{h<D(aH`tu2()zp99=f5C2g!c-'
    '{=9_Rqy$<b!|JBLxqF4^hjP9-G#f^@aP8Z>kmpj-'
    '5Ve;<ohioq3NO=|xcA!xps+$&6o1hWu5$rF{)nTHh1jr?FxA`N5PDZ%wrxOU(x!1OGMVG<6St>w`Wz{K$KI-'
    't(T<HH35#$5PK5C&Y^#;E$F%T%W5}8s?)WOMMouP25dZWC%Z$TLkmQH8~$#g?s@r#6iKSM$hBMzTI#9lp`F{eDE`BA8nl8Ig6#NS'
    '6H{-^)0A4COB-{aQkn?^UWv8Pfg9B8hqylAFywX{`N-~%}sF*e5%3W@TYq%)Mqy@JK5&$_x@u)_G8^QRnESiSolF)-'
    'VM|?^>>e4i{AI}2dT9tN9&gTOP@gcM}G8k^pzuH^CImDFv8B!nC^Mw(Qqiegfok}>`B`_cCmDJGjWYOIK${cka?BIqeiLg!*IiLj'
    'i&mq`7`LvJ{!3B#c~YUli0U`WwdVl9<r%NJ(uRs?)y=C+Iv!Xo8W6@GdgcYOjMu0V9@M2S*o8)Uk1NV^SRD^haThb^;)}ZEqmGPv'
    'g~Z1XRXIGKA60edSCM-VqFK08JAP{pt)cilGz&iV*8)6A&obvVPJ=HF161$4>a}YXuMtj0qYLem^rYpaBCHh2<L|-'
    '($~z!hB*#fdxp;oXTv|kHJ1LXGr_^#b{#nmuC?z4pG%%)@~+6#OrP4b@n4NAo9RB|5UYBrKDUWeTK3V>yLEkDa>_I7n>@R}06dyc'
    'H1*%XC3VlSl9!meakv@hICSul(kF`To@O}1Cz@Xn3)G%?Zk~|uH;)aTWq%sBbHR=I6ntF%iM>+XTlf0fn9b9D8erb~70U&*e~1eb'
    '(~6&mkF*nu+Ea!cx^@MQ1&bB~!C61*qdv;oX|7W(y!euzfn(RZ1O`J^*|*nxKscme0l^IS^|TS+us>yU;eMTyXC_a5?>_FWdsxV^'
    '9r|!)rYB!suioKHw|%hBT6ZPqu2HJJ;kId(O826JOPM9SC+BC)A04me)$TnHIX7}I;9+ctoM2cLe;`<Ma=??P8Vn))$9eowV(rl%'
    'Ui`8h+|R<nvnPB&@v1%LjyvvH?vd{#7x8y`3W+~`KiRq`{1^PM?-}(+K5O%)H@#`!KGAV+*+X@IU9-'
    'kdo%y3DJ?Tm3_5JTThkEqL1Cz_*oa_7M{x5AC#Cv?v^!i~lqHp0j_HiWn+k{7F4s1V~(Pp3J6YypD(lB&9l5;6PvF#c8WJXl-'
    'W5a#G8^ufMtpkhn`L({fSBkw<{A>2!q5RlYpGoJpBQxt<zbkn{<*Rpno0(<!Reoq4$D<!S`E93}KKjLE?%f&rWUbC?cHfcSlWg#q'
    'n~`}!9kZp+KW+ktM20vxei<2xk%Idqj~M<zh9lN&4ry=$eZ29FZ@e~ghT6yHYxvB4Je)Xyt(P;Po{~Q+4#t<jB%FshBsK-'
    'F%6Co<1q?;MB0v1ovL~nW44LR%IFLg!T<hLE2TeblX)o&B7(5Z4hHqyt;HM;4jeo^|fe$#?XgSX6v*;nak~l27sD3<k3H6=}`*h%'
    '@QhyoV*^k$pE19MrB|otI-t_7`iC(cEW7bjg0Olqo*MRKy=~ZyBJf;ueTnpy+;1~QWd9`%j{$!qqm_)ocu<vD$7nk6a_><}!)ohF'
    'B)y(O0rdCuAAPyNuV7;=7Grl|U=$*Y=uR;5>+#mfv_tk5=r}5o0KiGHbl?kgIvzt0E4sVf}pK~v|@D1sSM_$1kQxlM5=4#f*sQG9'
    '<Mci~AFNCX*!)KqD_dWMvoqaQVkNeIZr9LD5$AS@0=QPjBo^jsxn=0PSp3F~OdT+DE;g8&J@tGJAE`UeDneeaeRqVwpUh#_FH_GO'
    '8UyXb3y_dh)xm-9CJuNFvY-'
    '~HWCfpI*9quUnQE~!c5PImb7it%ANaUEjYVr@SJm0@?1A_x<IjIRtU(DqE#IDSFCG+0qz3e1x3nnxAOggvi*pE{$m}95svly2zj3'
    '-bNT6VGdB8MCVaY)IoeM9R$eWk<{V?I#lrQw_ORD9(tU%Bve_@W$gSRF7owuxP(x2{1<UvcI#qc8PC*^_7fh|j@~B)8bu)G@_A%$'
    '(_50~B5<{88jdergrfrj(!AISOLC!OOPap)a`mom$l7(a&5}aM6AIQR<KAMCPugXXebS?mNPbg>Q)OS$p46`q<qJ96CLjaZ$K-'
    'dyUxN!LC{(I9As;dM~#wlBGUs@`lwK!@JChv_|NqTw2`Qmwd^WMAjYC(eb(ez|0?I-%6clYMsa}HC(Cj+E=eN=PS%I)6Ze_O4-'
    '{l>t@%1$OmWZGn+?l=g2oo|NYikzJ;IKlRAzW`qFZgGcA|h|CWq<{X`eoSZm0&M%Oa4&S!+POuh2VRVNmVU+iA4@*ftt)joLi)4&'
    '~_!MS0_<jDrvw`<SreM#RsaiTfPu5;8fx4o91TmDG*EQCwZMYw4CSEaT!eCWKU*%!~_kH#mBZ708xi@D%TdJXE+gf|*F)3-'
    'ec+|gzFB6Yt4J}*qsQ8H<MxAwR8Gb;vJ;`GdSBTs%?`6jrQu3Z{ETiAo0eT^Iw(`RjF4~!o;>ZyCL=FjVIBBv6DePE8tl@GZQa`!'
    '!ot@z938~2<DvnAA=_%Wv=v&cvPtX`+Eb-6P7V3(eBOy$5MS(D*L%!1ZKR&Q~BonAcFFa6^$ik<CqBM+hT-'
    'Q!Eczu~&pyfr<qIsTOW-@3Mb*;1dgTA%5caosZFM>!8NfG?UAMsH!aFeEhq)|<b7%BOtFQfoA770in}8oiyC-'
    '{G_L1b?n}N*<TJpS>INar?fLA^)~?jc?bnTdjxYkE}(y2ZKu8xZL~l)f)T8`6YfFcz9|9nm=LB>@n<Q;$m29xRt49>p~r~E?gt*o'
    'ovVihNJcfcjVEmJNqAu)jc-'
    '*2$rj+icIly_%|GzI=IYWSl1spM$aoXI`)X}VXuBl9f#Nn7bXv9teswKWxM+v@kitq{%F+fpW%<nk8Tb}{jzg)ZRsH=7V^WlQ%5#'
    '%?(Rb;|J0f}XN`8ODi0-fNBm=t`ewp2_4cD%@CkZGukc0AhaB-o)}Ql|uS+jsEfp{I=etfE60U9J-'
    '7d4a9Q1=6pZLTlw*Hx8D({mFD;DT_LOA@`(_9xD=Dsz5l(lHy1-'
    '{JQ3mc&Gqp$0Qy>%Sy0o>lc1JnPaFZ!Zf!@|GF*@2;oNAYcDZK<cg9i2DV>#{YccrShf`N0Pgzl(?2yv*kEXiZt?WXL8A%%QPfdZ'
    '#|ce6RZd`5LxkUU71Hy9Ws!G^bdtoO-'
    '=|dNTK8a~}tH>Rg(Kr6cb33XgCuhhkLgo9+bvIZ7Tu<RRvc>~Ujz;`7E2DmI*JP8L7t{`>E5n~n1<JJ9~Jd_3|?k1uk}45RgYr}^'
    'HKEe=`^Uajq3m$eT2Z)MBQT$`R!=0jAB#rNO9zi^{u&%epM8M%JqHofX!{pwe@UctVt8MwwC`LVCP_V@<4Biy_?192W+N)8mBOI~'
    '1Rvg>uM*AEVfpFi-@({&E%=qC+h$IYp4IUThPw_S3M+FW<Wx9a-fQMbR;AL(bTK4;9TV^5Y@(5pD0_k_gWlYNv^yp!wu$VWbs-'
    'B|4AbDr}Y_gF7voI`WVL#Mjd5PoQODegwDs=aP-'
    'UJC~jnb_agv#Y&6*FW%?MxC9t)cQa2@78|hJWsgsBv@tL`_{+&t#m$E@OJbx;IG=NGh=F_zN&PoIo417#7}H2hd-Fw3-'
    'QA$C&9gU&9KO>C6c$Q_DD@GeS*E1Z!Mod94SwLUBV5R#{g%;9Zj=D&)hHaa=+5kK6$k>hcwsQ@B#Qya3eOhY)S8#Z-'
    '4vS*Rt!_0k@@|Z(r|obtK{a`FL_-<iF^1t8a}tgtf2tXX=4q|Kii)k48<=nKfq?TFK&Qveo-'
    '+4*ltP!WxuAr=|%X0@uO=icNx(B({t1J?0vnssGr=Bh9aoC0*2)8fRYiB)t40Gxm-TCNEM>Wad4jf6=HL@BP*1(S5!$Ur?VP@mKl'
    'N?Vsy0@q!n;U~k=_Tukf!?z``9eVXQTWnRioZK3rJrx|_OyPq*1jc=x=rq=N3K5mk3(W!YpS>omOaRCpqZ;l?nrq7wr%HJY8JP2;'
    'pJbSu{>!Mf5Q5V0$2<T<<W#zNMDA`=~N42KSCu|>RPo3|+8HZg5%NLK1*{j_v{h!rUu+wGRdZrAY%{(&)pQ`NM&blOvnKxS3%k1M'
    'k4jog?Z~FlJBK6{8Cb=4XR5A;H#FrtzilMr%02zwef_sR+<PC`-'
    'GKVL95ctsLUpEfw(8H9^HR_=E%^z%^i5~G~`K+)pIXa_{WY3){|EcqY)e?vu>0o-q%6r3IrrwdR2G5=6l&tHFE;?eDqicg>-'
    'KpV9&+Pbpsp01@!~5`$cwAT~znR~kTBB)(RM#hvv)s>;>xI53x#C{Lj^vfO2Yyc;;>hXj9BaOddpFPEN$r-'
    'o5Z1f<Yd_dGqinra*Y!v<e-x}}!f<+~#qbqVhu!fyEDxXQ@H+g&eaC+}cY8lurN%=3h+1B~F!U%%e(}T`<yiYU-Ahpq6n;%TZy$4'
    '-%iQr{@)50h_e~9~p6q-'
    'vy%yLDxdn7z+{<Tk|MbZh*Nom9UBi{!^3)a0^NfOn&F37vHu(nAtjo^xWT(XR!v^&CiND42;xAmmOJ4GlUIW27_+V^Fe4~+Tuy7#'
    'Zk7k^6oKO2*dOP8I<RSY${F(g9krUXty7t=9Uw`QfEe~C-'
    'K7GcYjCqrdQ@|_OLiW$P)#FbsjJ@9;CP!9J30#uCZ2m`%!<YrqJ>SCnr(Q3)0c?7D?(qZ6DjU3H_YJjorZyseVDj1cjPxkA5$ioF'
    'GjHhhT!WW2K%UdF$csLNU)PiHuDkB)SV#N^>ryLMwr{8QNX{-k4R@p#51*z^*j`PCaYt(4`A(zfZRd>oO#U-'
    'n@P2(atb2Y9yhB{!82vbxL*E$piC>)=ZFEdLFINjbr(Yo1#U7+yV(QV`*Pa<jV-DlO3uUHPc;4vx)VprU?>dJ+>T|QFiq+ILs;i0'
    '3dNBE;@VryMjt7N5VmD!5Y`%I0`E=Hg^A2V_@kg5#e{>T5NDT&`x7J8wg8#4aM}GJ_urPTl@Fe{mtPghN|6}i7U$kG#`tkpaq|7W'
    'c)F6XoyeVdyyNzHmHgQXoSqM^?n=HsEp<EiJF3sIC6?a+TCM~U2YGu}wK%xgl5IyR-'
    '&wAGL{)6CmypHer{%~HOxpp)6tb46h4V+vv*Ib*==Qxk^*u9U<n2FZ@6!`(O4!;cisAE|2!5>Tf2(6yT_)+BksD1AEOVOl#5_3Q3'
    '?xNvhBaqYdHr=JC4chZ#@#1abM<W+=AAWS_iGm-od+;ARSm-'
    'z7N9G`<7Y2Ffen*~<m|E+THGVYn%uVnkIjZ6cBhL6B@uTLYE%;H#QOs^R7C+Lvi9RhJ?emKV)8Ci>9E@GhF1GZHAIUkA&$^zy%?9'
    'wk9r)3bmtOR{Rs2ZYUVL<gADwQ&k4{$j(a8?{=yD%^B$vJJt$oDQA32Nog#KU$^ZWP@zx%ttyUY>Tg&&RigiXKXG2IV-ghqaRAKI'
    '+(Ble|u82v|12S4I(2R}mN8{$XZ`%g}qT5k16a&y-'
    'BQOTU%hmtq#dj&somRB=S+ea$<Zo!Y#n3)j;V;J=lt&4u<XMRSky6xc=esppj{HXl;o(rXC(ZG+wTOEhzhl^1MKk|R{B|k@ep!fN'
    'j_|fT%AHj~`MleW^usAaTX8fpZzs5r{iv`c9KN80ny%CSXkMN6F2Ylr5#*g^Ge4lOjk-grBA32Y7EIw2d1<O=RR^n;{KjJ6N_>ug'
    '4XK>`2pUJmAfFHqf8h`dT*)i(T`rNH(uBXVZerb&#@l{4o=Uw<wzVmFv^fvG#_<-'
    '2|I+kmmGJL`H;fdj!?!}L`^aa@1d%P~jd>#CVpJp%Q;)yrH0L)&5MTs#xqw*Nd(EjwNKi&KVKO!gfwk#j*%4ds%lVS2}#QWves@E'
    '2qb3SMM2xcWtTz06l)Ov7*A8q8c2S3tJP0hsUjm~d9gdg46h96}{)xc#suLWPoZ7cnVhnt3V-ODxX!jHxb;l<7!b%`7Jk-YW^KWh'
    'G<+xWluAUvh_uNYFD4>5<9oj1Xc(homzgOMNIx$+Z!baE_y<obrsL$`E%3BF^$)L547k5<9l&h&I8pWP4q$Tgu={DdvN02@D2o4C'
    'f0$otrvV$t*f+66yivzJ}oJ+j0D=AMzafghnSy)|Y9^>vl4whccz8~D-'
    'I*}3XLgCCh;hUeK6TkxZv+ahlrj_Yizi`#}Dm2KTUqYvRnbx#}kkyxR;4(DI4FdG{k=A7C&cXnHx{<`>4ov}V2CI1iMN9Qa2XqgY'
    'd4w35@{79Une2l&LkytHWF1gfkI{Y+Y@_p{hm)pp#-GU#f73>;HHbK4qVr^@C&s^J<x{htw(INb3s-'
    'N4ykKX*|H%EpoHAvUMk2)STa;rPOB1ilN_)%u=ZQw_I7_lxk`62wMbmm5V>0^K&T?9Xp#{fU#GqI`IEi-'
    ';J@{88^(fN!Yjrko{@FTkGI`|QLg`dbap$FKkd|~#LAF)w!iEa218qWC9n3eTF@gsVGed64*q4`mx=fN)gsQGTjkN9HZvuYkkjQn'
    'W)h+V`NV$WyxoS)2oWV7?(^bJ_!N9;@fpFVNLo4vQ5Pb}*g{Am7r#*aLb7i;{8Z$9Hk;v?jd9)J8{c2XBk9l(#&A7$1?V$xI0@(O'
    ';Wc9@M<@(z!0%w_cb@z>dNqlTvGHfo(4!${BW89#Cjqc2q3aQ0V>$Mr<!@4}C^)%Yfkp7<ABn_k2x_&G9w9Og@jotXbK`dhUwr(@'
    '85#*b1LZht)=J@30#*xOG0$hE+aMla$k_z}Dk@5@~wH_{Wu^&f*D`7ZboJq$aV@T0CZIu<|Td(!XblGyvQxtm|on=JJ%=*a#_otC'
    '}vnqBx&R^)PQx6~g^GUp0@L^jI#-G(2@nM>bpyvTNg5#29-'
    'q+V$oendv2D_h4S+7JBbe8!LXMRNY=#PnvKd(F=HQLwYvJG=0soPl6QGyexaGF!8FpkvE))tCX$dHHCa{%Yg<dk#}DkM+6Ad>(d_'
    'xmWhj{wD_Le$)4I-ES?jW&Yf0Zoz^Xm2AJ&IQ~uJ*W-O{OBcU)4e#ht&^E4GO8s3^UpngQdv2F=K))wXYM$4V`BAC$Q<v-'
    'Yi6?sBwqAc8@r=(%+>BjBZjzDk!TP?=+x-0JKi_>#)ztB0)Thb^q6)~BF)O8Q7CG_iUdSAF>%d*x-'
    'neP6yVcB__Ce?)zB^wF53(=o8tBW5^tc=R-'
    'o3!+^O8Y5?`tjN)5E|yllxYDcah$ib6gvpqX*1moMY1FrtZQa*iq=h?x4#&isP|S&`N&;K7rcg%q8B3qul3m&&_vw+j$iGz=M2NG'
    '%Wdbk(pg)o;kz*78fY~FyC+K?H;{^&SRcs$7|Kx!U|&drJsj$J9-'
    'cIe6KCNdLCEIZPhpDWc6IrPk((eZ}BX0ke#b<jfE#`uak3jG1Ue)pS<<0Z|zx?v4v+$-O@ju3}r)<Ug-'
    'Y7`oWJqSmtZj`MS4?f!z3hGk+vANbn`wSl<P<q1Yb2O}sQVb$V=j%<p_XJrhO`#mix%n<3x2N}aOVO{Fip&jwu08Ky(fZ}bW89xC'
    ';jt=rZ!uGQ=Ff#>;lY%+3;TpRTzOD~(!SD6!gImNcb=Q?Nn5PdSYR~(egCU4{i(ChGz^b#Ahh)<GN=Uj<l;Bgqo8v9^ldmet28W2'
    'ChM0~HDW*E7+2it{hJL;aBZfKT1mA=oli7n90V&P)oY%DRfX|}H!mfaIVZ{?C{dwW~eJ#L*V51WS<>eFn-'
    '$(Ucz`==LO=%cTnxUVJ87@g3IzpJ+eeWEtoN<ESu5qJ<@!iS<`Jm(RAZaJSVXT1h3(b|vSbG>!;I@dQe_{V?zM|rLNovy`opr7+h'
    '7V>vsq@z!mJ_}^pj6<I49X4j$bWD%!8@iRxeDLgz-bszW>W2(>5Wi7}Qv2NXD=;E-'
    'w9rj#FZD;3`XjM$_mN)ve9h4luXQs_0slIiY*@XiecuN^_`&u+_2gD7Fls6ntS)%Tm^s^@jjzawZTDlIi8uvWVDTf!2G;`{DjKS<'
    'p;H$+e(6hJYF?i3kzI45+HSHh_DhZ`9wUpyO18-AL(g65TN;@zSJIh62hXdGbH3a^zvxq+`c%shd5L-'
    'p>D^hrQ0wq9ldNgz$GwxCenzjHlN~x|`5W!M2me`UIB-&Xm%5GgVQGHW^LRz8_U$s$8a|~DJ>C+}(OYuv-'
    '7;Or=}HgwbI!%6RaxuF?m4JG?vU4uj3u|!1IQN?C$N9csIyeO&Ms^D#)s6ijgOysVC+lxP3JhrY@^Y?uzONDyZWHZPoOXL-BjmOd'
    'Zw{^y)S)UXy|kBU-'
    '@1aqYp@W0(MVC*DL4qKmOxCuE;|<BWz%2kB(QD9PCKUL{4?dDt$&e7NU0mtU*jdjL{5XaR@k;o)!9C(~oBEuD>h&@KdwG=h7F8?_'
    'AG`jrW{O^GJ&C`ufYK?CY2BHRAih8`r&DHhKUhR|wyW!^jgSXV6wmExIZ>BY3(#w_^k={_U6qf7W%*JRrwck9YnrECkN3rrqnwWH'
    'AQ*?IfGqj$|wFVd!&lIK0G0T4SN?(e%ukdy0)&>GCO@7dXwu)KjE!tA`$XXqoFKM(-'
    'Sr9*tM#9lC$9Oy9%TM8Cv>%xJ``qeo@S3vyXqlK3AP#WqSFd2GqV;K&vWUpeDH{nI~v2KR7{W~%6KC+4Cr`tWlvcJ=0+?4k>NMDM'
    'dfgTW=AH1Wo{zs`ugET5%!Df`BJao8RiH|C$U?KE`pLc`H_P+t7P8*~Ufew^hE+-'
    'megT6D6Wq;%Qn$C`S|<+JcLeLVXA(s!AA(Y6O2NOr?eO5Ao&EP0sXQsQpzJ=n+SN3+a^M<;f+xiT<Fv`Q}SwmClA7TSs7m7jD*_c'
    '@zn!Gzm(?v9#$vO~QhJ6rz4n8ld-zQzIght6T-SUv9Q$J}SFd<L>%Yi<O-'
    '%p67Mc+4khyonxVzp*FuTKmdZzOwQ8XcoL}s?RbHds*(?OzmyU|FU-'
    'd&uk#HCu_yh%Jx~}`*P*j!elMF(M9C1$NVm5hRvg2y&48I|HLOgaWd<4*d7^#=Hl;L^zT|Pw|xdr8$FlF@}6ls^^@)8^VqO@DNjC'
    'M_vlMKqPgHREpD=Ax{X-'
    'p#h7QYt><Is!idwO6S;1Udf8>g??T(rcdYx>>Z2@whChRbwGQ^rH_vw19K8qn={TEmeqvYaAt83GPlq~fHX|ETKlWN=_}%$F61#N'
    'YnQ@<WEZt^4op7X!F=MxNg?`EGRJ0(A(T%;!r^@Wu^&+>?(0knDi(mZW&IyO#$R+Y#HjjF&sTS}Gzo~Vdu+)xIm+tCWa`>CgCq8W'
    'kop}N!Coe}FN{@wZYDd3}*@C`%gAbGQyY9Ui%yLzGbfG_@6?*%9qF*o9JN!ztZ2KRtxK8;F;!E}(4YJTN`8Me0EP5mh^*bB=zt(+'
    'yySKr}+qgnIc)7eceIk4|{Xl2aRp?Q__sp2m1D$(2YK%|PquE}w_vJB?A#^W)6`kd)zW@F2Z=552zLF!o4dV)qk+^y2JmbV@O$R3'
    'yCLfP|Ojad-#GYGzM;oz+EPq?cYtH|@SAWv7iPB?mo&|I<_frc_${vveN1kN{nCIzPd|N(C_ppbT!|K_{;t;SReP_Ln|Ha-'
    'G*R1y}Jt^Sq&cfT?_O|YMt8Q8>LeDvPQE(%)<vRy25`%^r&A5?RHmqRGLF)Lp?<gOluiN*#7q(V%n=NO;BOOYYt{1z6Y#aW5+wUL'
    '#@P{vwhZFpW46pm?IwE>Gd4zlwx)iPW+8z_D;NOc^(HZa>n2&zi@^<C4!kN@NeC9Ks=^2;uQk@_DMa|}dxv6hrAG5#UL-'
    'N7c*>X@aXB=K+rUML~uTlQ|Ilq*>D8DmH{k2E7w0>RY8$^GR`}Qv}>MVYz=Q102j$`4Qd6sf`rfB5aGRw91io6gjq7Uez#L}Gq(o'
    'uaL*r=(0ITk;{7hXH!&j<0N)HURsW{v*5PYV1<EQf5MZ}d;+f0u81ks76&;72f9vY!1p<3}^SQo|M5x5C7G*6tcV;y2@Oa~#<A;%'
    'xAm1NhOM;74*wZxcV#SD#LI-r0n7xEQ0pl6B@5dt;3sS=;a<G8PS-'
    'PrbJf;YZfgYyBemcE{jH&f+on(H0-z*6<^7n&=<8HnDqu!;eb7ZN-oDB`G<+6F(aGZ_7NniDcOD;WzN3*c-'
    ')jPc;1K&awEB+%h>dnU^7ke++&kUVjXJB-'
    'Z5YjlTD>GZy@)_~pLpjpln~*E+lOFJAO0cF)c`7C)kg{mzG*@uSQEX8*~#R%=xE=$v*uG4+MvL2Jz3+=(B-Lq-neR{RJZr`dOjt8'
    'UCe8+}erN3Q>U<41Dq;3UD1N{_aEEQW-~6Z6=H9|c27J;<2#)ZZ(2%l+zKD;}v1O&{T7@go@BHvGu7v#H^khw!5<bE1}+-'
    '|!>#gZe&+nZ*y?haXwn@FQnR{09xkjN^_YT?aq1PqS?^W=Hq+*4ax9WzzuWk7llM#*bpNqc2|Hg&)yFWn14AKU!w)_&)tv<s<0<2'
    '|rSYvI{>-'
    '9g_MjwA_XtIjcplo%oSFCOJ=H*?NG(72f#9H(tSyQY$xNC4El$hU4#TSTsGd;74LsYy8NpnlVe@{3iGjnSloGoB#4y;74o=zAqZA'
    '@gq5>=7za;`Fr%7em1rDi>{yXBYCW;QyMi=Cx>zt_TfjRTf3IHu4kTStaj!Ke#EaBeakM*Tv8t<t^q$1|GjPeNUrS~KT=0i{$uy*'
    'U*kvSshMX-zLmY!c<na)h^!2LB=^oaAmhxRA%oZ*@G&tLn3Q@Daw7Db@uQD^^rIIekN$MT!V}}|oX>6ek<Ts}*L}U{d+~<E!u*bB'
    '^mB(F)qZz>F*-bTqw)a#4ZDNclHbL<$!9o-AMqF2ulDe-{_3w5{HX4suU~$u>;H?t_=~0=8t=f5&S(4xy~>|#z8AYuA4<-'
    'kE!yK@=igprmbf`T>M+-F*4qEB^H}3Y^0MGZ`mw>u%|Z`;q^@0!X!?rH_>uUc`i%R<kIW~6AC-'
    ')~f*<|HZ~VrBeT<rBH3V1aMlQPlUHDP`-q@#j!Hgg24M`p*PLW<ngJuhUM6OzR3GM-'
    '7lOwISpS)}{$i*M{{x`*sQj?VH4$amx8rJv`+otqt_hG7i2w!y$;R-'
    '+M*qHkn^P!Hyk4C*+%P@WvUFJLCM}t;(=DwZD#bKis&3e!DLSgsN3p0Ks4g(v8MZ%AgyFKAY=hwlH<{mHk-'
    'x@#i9VOS!<TyH;@T(a=a@}Ur(0Rd+VEK5ge8c4SH)g^HM7Lw{BRy8qyJ@XEecv|xNRAQg$YN8}wfUSie!k>j&;9+TnvSFKBTIbRn'
    'x7l}JkTCi3cFbFBfYxW!hYOGdaDOJvhWz2M;zV^!u0CAU;K#8FSf@HBfs>N`tXN8ywOi~%p7XFcNcy{F7c=D7e899Wgjxz`6l=gd'
    'Uzg<*7y-Sfh|t19fKd$cU?~N>tJ~O*?g45#l=*`jdONkRBSlk4L_=LwSgavx{UMSj5oxOw$&mv1`=Ii)*M>R_z`>eI`~oDXX-Lq-'
    '+8aIb^t$OYhF&Zy*+!>{2MbC(F}j_>F{{{-t%9AAC(Qg;74Ny7OW+;xQmaRK2Xt<L*8#-'
    'M`ZF?P2UMWI$z;$8~9QE?MyU&lsbO&xGsLApT@dhX6g9Gk9N!~?)RzhF59lZkDZeKd1Iy(8?^gP!jCd9%zM>Ck=6JUW*_{BtYkO9'
    'I>{pTNbn<%sbdglWvB2h=UR;P+X<~_nYj%=!fW=}8O%9JF5|KIk@uDyUuIOLerAf5T)~f$+a~sdUVOXE9p-'
    'PdndO6v4XeXaW1tr!UzN^aYl>s?d)Vo6P2`TpZq`FB_z?`RY}9kM7R)F$qoY2waic8QQRW$}@gworvLpJ;20scG7W^m}(jojP{?+'
    'jJ+m{c1#5PHd<1YM&J>q;@=#_;o>~!%LHA>>5Y+XyeB3y_~Wmcqqa&ouGLFe22LiKUp!@q>Hp%+_PotJzvK7qInYzbax!Ha?sd7e'
    'L(Wky;SUgo>XgIME7_B|L<VpRL^BhO_vocFtTeO(@X^wAkVIv@B^*Uyi6yv_e)jy)C^WsjxzUHUQAV`ESB+lV_~I8U%f|Fbu9k4A'
    'hGTsO<vlw+tCMo)(F&(<;3#PLsd*a0UGu>aLw{mSR8GuygQtl0hYmwxNFe(Pe+5eWUz3;ozu>{WlK=NdaN{s6qm^JEtqdJNu%e#5'
    'p;e*yTq-'
    '13f351%19wP$+aTo>DUK=f^$L`IeTx)}4`+3X#^7<TWHuQITrrXM|*x>J0ISINS<|K=Y!6C4Dc$gB9S=uC&s{TcMESYbSgF`mt{?'
    '!1<M7he^t9(`gSSN;=omUB_MGIm8j>RHYQWaEa0Bc}piHU9-'
    'S8hygsc3~&fnOx|Tp4epk6yIvxfGv9<zITPD<f&dT;?H7n?Di4&Ik^TNbSQRs?8-'
    'b;eoEtMk%ME7sd>x`ZiW_h1}}o8qle!|Zc586SjxzQS?mcuF5NHY#3tHPC$)DL=N`Z4B)!<!dZWKp>tJ>O9g_Zq>?(RKc?QWvj-I'
    'BM=lUa$vwlt<h*&)R92*j?%0}A2D@x}zEu8PtaWn69o+ug)8Q6S@er1bv&KSE@?pxU-'
    '^ZSmW*%jKbqtJmp=bG8Ount&}98Gb1xQHdzA)e_GR>Y>DLmBg8ad4D@O)Nd@=Kghw)kiO9o_tn*2Hji!vAy-'
    '8AaCCK*0;_yY=1=@t8{qRw65_Xx+0kG=ta_>>Apr@*1BiO)-'
    '%K(f|Kzpoe8wzW6MqFZ)bjwyiN3i1;J^=c*On1*x*L+FMb#r`9FH$Cvy?l!(I<t@<03p4@tfcK8^i0=l}RSSbgI7Y#lL!*xo)HAB'
    '!E9owoQZWuJDApE%FJhxjdhj%S~Cobjgl$3On@HGlPd?}>-ok7rNXAN0|i2tH))gSc(-uHCPDg%OQ<tgbl<-'
    'NJ+6KlJq|c40444>4kUovUJr_YFL)<1esYKGq?b$F5B6EZl<qlI8o@jqbJV)<r*-'
    'Zf=YNUpe;!r$7UK;6lUVO>v5y=WyizUdC6D`vBACFR<a=qq914E_bb?up=0V{z<hr@RgoZDt{D)Z?DAoqCf2i*;qW>eFD<IK`#M4'
    '!Syx&>Q}$2zfR+F{4qbHhwR33uHn4mE))Ku?@0TTc;9!THT%45tj=*Q-r3OWB`dlova^Jj@P*tY`<5PWqaO5Z)Cb%-'
    'PzN>h^1M$cTQH=~cP%?}S6mw%I)9-'
    '2?Z%P#>}rqLssk_R_;}`@kG=$_1NT{GSVx}>{nMC}GcF%NoV$Fh^AWde+Tnfl7&8?%di%ZM4Q~*q?>;)_D#3M}Prke7{VpEiZ?Xj'
    ')<Ta?N(dP@MG;;Xt)v|XbKfBMl{&Pbgbu6#0g}p7l*)r42=xMHcV<DMuog9DiTE1raj~D3?ps$JfId#unI|cW`Z+uGmh;k3*8o-'
    '*Sd09<A^vojfEwt53jm#FCDq1YqhW?{lc;hTHcr%;Ed(lxmn%tC&OfRE9SwWuGUUlB3o|whomwM@o?fVRIS<mrp6X(YlUaS7*UGI'
    '8V+m!C#IhlF@Y|KI0Hn)1n51-'
    'li<2&B*j_wIpe51am{Ug44=>a}?&tw)aDIfl1^sj0ji@!|Avqi1s)xa!D|1Ej!Wf%3mO!~89_3Vg}?`I>w^vsMI{hP=R@r2@=o(r'
    'uu%^4Uy`#N`;zAPP>o`#KE%QYxIR@;85mQ)TZyFK|y{6DlBbvMZeYu}TvIr`dPWU)`DHP<*cZ_Ayrzs?33C?CMSz)978h+Bwxs0B'
    '=X0_{R83q8}jGW28r;1@X%^BEm|71iMNcd{GkI(iPjIrn1SWjBaBUF^Zu`X0n&VRI{-'
    'r27KvXY}yH4`1rPPmYjRqc)+J7zTd{P1KTD&gi_@Rpa;2uKUpGORM&%<VflcT{r#NIIi<+@5GA8LA|_2e@HRT)be&s8~llFm>G=W'
    'MRbhJHdjym0-Zq4=%HD>-MWNchI1D^#j`qAJbYljbT9Yqe#IU=@=c~b2wl5K-'
    'oVOB79=NR!JG8=F=Gv1);VgP@EWlOe29+0mS(JJ#F;u~J@U(YkMV*%o-o&wF-N`sE?#W9@!Rd2GhH&XY0Srg2MqsnS!@U~M|Ne-'
    'G=8kV&u1IO_mkanZOosodpaHcVwSTsdR_Io317Ik#Np9TT-O@4LcR1@VvpN*@jp3pb#^X>U%uGv;-'
    '})OiL=tRb3M}<ud{#VsuVB7?iarvt%kqU{W<N^m}7UISpaGPqJPEq<x27c^#|K#Pengxq3bt(<2R;8K)<QXU&eoJU)6a?4B;ZZ$0'
    'Lho8s;(Bh5HJ|>v3S?3--(BPLCx#;Pdbsp7t7awI}mu&h)cat9~C#e9_!(G8{kgAJn6j?br7vC+3g-'
    '=#N@|+oRE!3~tfB>B#F_$H|(0d`-'
    'MJ`!3^u^kr%~8z8bD>_|8zK5(!22ab_B6zQ#&x|k_vdZ8^E<Q#@J=qUfdnfK^#|6A8@g{Rkbah@AEX6L`^?<#kMe<Gg1ui|^Keae'
    'RInv2w>u?b7Ax88S##mh&WxaB<FsWZQhF*fb!7w31f1^fBb%E}{9+Y0aC%iBBsNdE8-|FF*lJ?Q(?Za9Bz(#-'
    'zwNWWQ`rLx9}#=MK>DKZ}&M(%&p70;%IYmKd^&WrsL47ko;;)zW&GK?LCPUwY~_^_kbc0VT$Q+(F8pU;B5ILB-'
    'r`93~tb$&Z%v24}$?a(SU`_3@miht-VkDR2|9rh3Z%llH7<vZMm{1ki!zi<s~C|E@>qPZuXvynQZHC~iHuF2cS3-g-'
    'sx_K|ebVu&dG6#^4k^HW;-'
    '<37$D&1G(<W#Ne@Y$(>FI)dKd2D7m48OR0(CYE4h6pYxR|wy+6U8vRJ~b5s*KL~eSIdTK+>DKdK4^jm<&@E59_dVV@%S>>kVnh>%'
    'hVLft-`l?M0YuPS?+^ux8`1f=^f~Kyj-'
    't6nPn0=6l^FsQRcvnUXUAdfAo84EL_f<IRfeq)U1_k?3fPwu5|9@hd%V7mNCwZ*h*HNrwe;YR{5R$c6QiRp7X!D)?Rtt^w{^2vss'
    'TF^Vct047u#*D{&k(a^<skuf}cI#uKc*q0f5p*CM;n2c5`!=Y?J1IW!R?UDI#8zG;)#^bY!6q#t4A5}buTGt)-'
    'SVtf<1v*TPmX0wfMi+*qz{8@fh?AZ7|i{6eckACPwKBJ%44Lm75r~7qY<NxTG+AOr3VubC(41eg(H87C9{P;M~I9Pyu#?&1*O~fq'
    'tFns7SLu{cL{eVX3>9uSmGT}>K`ciPv*lri2C-'
    '!1<$^V>YXdPX1_5|d;<gGd@ORvNcvuGRGybv)(7$Q5C4G}+crXODePRmc#51!8*A8wLsC$~^zv=b{ytuou6PGGmnfu!r$vHW}f7G'
    'G7r4Z0z9GV{+|H)GA1NB*DsRyFwIaeT2?z3NqMYvLt*#%|P0hkeYqFW<EP5BH6&n)5qmZ^_FQ3++DRW~T7(*eRo~;oeQ^vFLa9r|'
    'V`jkk@pc+;bR_yrk6B1RJsZ4@SiQL`(4vcz~EcOhgW4aHGsZO^>j7W!9&a`K=xYR@XKpo2YE?#?Zvh*!A#mGvLvKU0L6u{uZCb$6'
    'fpYXIo8}v*}*MRcqfj;)4%A{IIzH*0~z^#<jyy#dF+0TJRIqHt6>uUJDmNFL*~VHkb%nvgN&3jC+M2we4k|gwIDmabP{EV3W!1ne'
    'n4hue9VRvxgJs3qJ-'
    'w!e91OOhvtEdN_<688znJdqK>z?y>18$0B*%Vl0tuMcb1d{qvJwzVtPM`H5q*Gaq^6k)CzLe?os)k$XoM3q~Z)2wQXSXp=gv)FGi'
    'O9@Hbz=lb7-A0;=ueOvhg<o>9oIthLh-{25_G}Wj#{SsFf3#dI`>|nAGKEOY8E$-'
    'PK=<{b@#lVi5F2$oe&me5Ou3PNA^{$$2*sQY^Sp}1taHH$s=UZ{Ax<7GqXQt;Fz>n00!I10~-'
    '!=G=y@4r^_55VL9AF9Zrp<^|udUByJ>PW4vzdFGe8KpC`X$t!w+)XE#eB*i>3viKW&hQY!AoGmuBG0$F^@z%2v5VcV7Pe7xzew^&'
    'SBTp$Wgt8zOL)Pm-'
    '$5X!zbK{AJKJumO3+iZ+tc}kn|;YjeH$`rTm?N2lTmht`oygUIIUtT$G0(hg2;Re~NA>8n&H_)}vNw12>X`?#$p}bc!5G4-'
    '4{j$WZa##u>yy#DKkS^y+W9PN(4$wS4AXz4Dc>Z2V~8yGt%;>9Lde?D}ot1%H>UT<F9ecm2s7V>iJ3@J7)t_Egs~)n|9l=Ft<k=c'
    'KSZ_-'
    '%YnJ+z9CyY?{i15?+P8scC`VmE4D#Cpw^8Z(H<mMgp<Mlou2;23@1^}g;;=d6^xW&<@YB2F)tmwXrJko#wDHT+Be4VVepp%0`yRe'
    '7tc`E#9j>`clT#1n8G*h|@}8}?Fc{P<GwgA!vH`M&P2=Zf1Oa<I-;=Zo`o<#Xa8K6vqA=V*{ck$=(K!90>jBeo-_-e<rD-'
    '9LKN*;~$wSOyu+PVxQkfB*a2W^pdW9brxOeDrDR+L$rFF?9^$0v)sGlZ$ORGq7v@Q1mt#v;Mkwhq#8<!77|f_doiT&-'
    'F=d+w%ct3@LWj$icfvAL^oC>m>K$k(@92)Of0R2EIT$JthC;U;gDZy(dFAv|>|+_s}o-'
    '&zZ%yvNKv1!;a*lu){{L+ogU@oP`WwYr7x%+3e%2#F>+eFBUImf==QnXp*_kc+vHfQ(ybq*Ot65pKYbz9bSvi82jGu`Fr-'
    '8Mn90w17pvqDXTNz{X9kwJA2<gfVj|*f%dWU<ubnz-PqxE?<eHh=nva+5DmT7tjO4JV@41j>~qaGA)oA<zMpzt+IKW^Pr+?c8<ZY'
    'ai5sVvRWL~YjyT?!VcoCsKd)hDPW_$QuMRG-'
    'j@!=|T%Hd<`VKff?1G*&Q`(FOI6qsPT!tUjIp`isiCLnjx@PpIXS{#pt!>OkVMAsXU;50N*H$)Q&Rw5p^Md5t%3r4E^$sguZ+=3%'
    '#2{v#Sl1e*_gdoYiQ9WFc;w7ObMLU=DDzs=aqiQW&mVl(=Y)*oAFw^iV)maIXL955nw%7}f6O4ELz-'
    '9AHKd=wn0dLe*kSZ@dT*mA|G4a@^dxFoJ7h)I<fsJ^XK)YvyWD^FJ#?IL*<Cemq0zpcb?ZKh`<Bm}d!t7WnLEtpCi~L=zxbf%d5}'
    'xy8>?eZy#(C|yJau4>Ddo;?^p06`XxFgJ~n-=4#qjPKWc>8ob)LCzU=C@yXmTdbp#h$Vt@1?|Ipb>d=PEJUo&2oI-_-'
    'M*S58bZo#8Qtqbhfo_CKkJVZzGt5S!=j^-o6bI_73EIKapSmeLR!C{9N&$f+G^uOYVl8ty-{6BhS@L=l{{+qdE?|a|-7GIoAqFx-'
    '%LFckL$zFO>TrfCMu#Dgs6JF8r>%_Z5=bX*R(t!(YteKA^W5;81xykDGNk$)owwK8=d^dU|_8R)6{VexSMwWefo>(Y-'
    '#;(vu`E#H9+y?#Rn6i8M=J<*~GV14A&#<xo-?*y(M@Mp0P8FG;c3aMhd=Xd+-%m^$&cXKdo%0-{881p-y3`hJt1k-'
    '8gB5MVkAe|I2iXg@quJX0!ZBBRqfcFW<!oE%2d68Y+SlgV;V}b$X+N)QHLuZI3y*a#0sXn?Rem_$N-'
    'rIBq_fkrI5zmmALdUqzp+8s_h^D{Y~ZqsyWbO@lq=;rMi0BCu4u-'
    'Ke9qYC#)|x&l|F%4d}_E+dIoxp&vC!z1IAwEv!Y?}qpV;@Yb<H1X{IaNCoz*rzL-83=tpnk)sZ{b@s*-'
    'u^MH71>SfX&qHLPWdQbm7#TR08Y~Y9a+h_16i=TSV*_g+2G5XPM!~mYaaps-zXZ+>tkDlX8UPx-'
    'Q(#N*;S)P}D?Hm=l!CA>{xi#JV&l#Tj8?+AyH?DmO4NsnA^x7J~AF~UWp1-'
    'M;nR4ai;<@+s$N6FS51*1vGu_gcjvbx%)@LO*eU1nIPoQDvu9O~M_%5=4s#6fR>zph6nO<x7i|mOW^&WJe@in;&hx+GDG`#mD!i^'
    'UCeap9e3w^lIZshqac2mj8R=RpQm5;mhs-qw2QL&*>3z&W*r#t4j?pkVz)%UX*?gwAWe9JX{x72;B^;$2p0MlbJkMO~)L)V_ZsC0'
    'odh>ucVz)qF}!XA`c{foc&i%Ty>x^DE<PEP0PH+|DL-'
    '2{U~GdRY@$n#GOwrx*#6dBEDO1*~|Bwqmjp+_<q<Qmxr>|ZerweOzi&!=9RfA2N(O71+H1#Xl6B<nh^*l)>;9KEoX*@nq2#(%Lp^'
    '@0%hR4XC2`07``dZAzX1>>7%J?mN5<`sS-`@!eK6zP?sN%|9Z?3!-'
    '_3qh}7MlduqwC4Z8kzi_Knd}f4hj<=;i~X88dh%dk80;DLi8_GTHL1}GKIt*|X7J49<qj;aZCH9BJ^_7@{uN?gVyR*ibWGWRODt0'
    '^=9XHSo!BhfpWlRU%5FJ*_~D29kuRP34z5qXOSq?AUh-N;ZduRGV1vRR)DGcEHWy!&FBv+@<z&C=mjsg&-'
    '?mSDE550mGJBW&r}dJnC60oAiPgiA(*xV{>~K7*zfSs8vv=8`?DouWt+TxJJxA}_v*ehvQ+LU#zE(MH&K&xP&8y3T8RF$&vgxrvM'
    's4e(<}9lB(KB~nec}8b^cIUOdtsRYDNZY<Eoa+|Zn0QCn7EWW1-'
    '(hck;*pKbFj}bTH(#~Qoy_DkABHTLqGO9e+eHZXHJY!Y+NlMS;9{vXUNOH{oB8dJ-u-sax(El&Xm0;yTot?eQq)vZ}A;&q8r)!>R'
    '-^0&!rYiTw7j0`dNCXXC{+;Uh~e-'
    'Zs48rRWD&^FrdHw>%VSaHhn(pHRl6wkW;PCQFQ2H&lC;4cDbgJOTNq$kxMO}!^aZ~g8w+{Fe9_=)tia8nlW4FYQY!bNK<?pj;n7>'
    '&nGDPlpZvZttVqv=jDjkqfKL1ANarr&Wc9S`F+oNRd_8w3y-0f-'
    'yePS(Wa+*HvKO6mUu_KkKSnWyzdb+Zu{RXD0R8ySol)yWAPz*C-'
    ';S(?b;=Jc+`onaor^cx_so`uYdmMe{TIe=Cw8!BwjnsZP=*OcZQrD{pa95d_OuD23k7g%Io!*nEKc)cI9vX_HU#2`RMPHT0r*Z65'
    'r!Pvro|v&Cm`V;c4i{&z2uxe(IR3({gXrPdaz0$LW}$cox5Z%zEoSB;^<AhnxAoU4vmxrQR$b|M<t}Sr)DDV0>f%yO*9(Q=(R5O{'
    '-A{+<TWkX;Ti?x~FXFGS19mt38EBsUzs?xA*?XSLb7*(<@*3%I?9hhal{w_<HF(U>3AEkeGzMLNEPQ#Nx?1v4!N)n<q2oNh~osIi'
    '=#zbg6zduzvArd49=ZP^)1^w_Ngp*}CT5%c9c;4xPF`^w)zE-Y2J|bXeEvh>^g6)as2I{f+re^UCw-'
    '8<f5s{1@^Ty~R14KmDL!F3!GMNpcAG=Dg8$?1iZ>S<_Aq9o$xIe)NekyQh1}kn>_s?0!9d@xqvYwDi^)axZ;v;e8!TCDTXmzRm%1'
    'pZxwhYaOFX?PAG;jb07#Nj=)cZ}gv6U-'
    '{5O54HS(v70kszr{_5oY+dYd1Z#jywVp*e*KhBv#SqsV^ny2_}G1~`j^5R=|OfZo+Xda5j`?*M9!-'
    'kNbyd#+=vCXe_sAbV;<=zEM6p+Y3NSaS)VJk6GtnZwA51;Kf#IajGVEqmoNR0oR#$E=v?YiL)!gCN)B{<(d*LR=n%c;HP1mo!}Ld'
    'jwb&E9ZNZQIo&N>HH8&Wq!e7K%@t5AO=GWmBvLk+G(XREY{1Uc7`qi;1$*8g$&g1X1fy6+|E^l3-'
    '50<z|<|Ck=d^0vaJ&EsYe`a5@ds8KrMUJD7&*rxb9YfbP4Sl9F<vUV4I?totM$dVUOlWv$d0q6I9w=}!^DBLhd(uZ=u1U$U{ysVi'
    '-@(e!PW?yvuubzi`Yer^4~<8l9i7ZhDIM9L<vYY>6R%YdN51*2ve#Sw(QV{G@nh%X@=eGa`%0#&T`a#?tzhF8^x^0g(Pzl@s{Kd|'
    '%z1YGS#$l-'
    'de&Xe^4x<nbMdU?z{cM;XQ*h>?+^di=PYsxpW64b$6yspUQ_zjd8E7bm{d1`#&9+HhVq{HzRuVOKls6x@8}Th!J<FXyHcOP`Yygx'
    '<5TK=#m?O)T?hxw``oMg-'
    'P#|rx_v!!w`#BCv9_#s=Frgfr~YNeFV=NO>5Y}SM_Ds1(RTD9mYddf1A6GYzEKC!{kKOCjHX}7E4ekDbLVH(r>^~E_n|IQE+IU}B'
    'RiSBQaa@_`Fv;)%z*6;AK**zM_?Fgor@=17T6Pd0d@?x2u=}f0v*v%jrbq@!5=iA6n*6Ic1<+dJ#d@_H=1jVf*GxQ(uLOB7XB<A!'
    'SCH0Q7=LBlt!<Mr6;U@Y3!;x?|qMA2Yi_H08f0y?{dP(db}pCz+Yky@>ls(`~|(;(2Y$lFQ#-'
    '$+u!Q>(<25JRPRG;Hcaz0o1M*>o)q$lyzlS-'
    '{_oocrSH&}Z=s*QdSf;AdN0aPkdOGqFMhExA$AV>+lSyp!HO)rKGzkcrpWL1%k{gDF~5Pm-uXr4uQXk2|7L$!PkXOVuHAwgC3h;A'
    'k^2@S;ExACO79#wzs1j;|HALne~&F*{zK1wk{7uHKe|}qM;HHxAMMAF#PRu1bHA`Pek4|X1N`XXe>i@0I(kT-XEqNzK@5MY;b{Cw'
    '{K|9xhac_7kLGjhId+cv&(hILd<(6%;71qNz>iM;H{eHq_jiBSb2I8*&VKIaelE6G+xnwt=Tf(SQ~appXX8ipzWc(D#Ew_^QO5^7'
    'Kd_>uUtsVg&kfw@<R<vhpZ(dNE%GjQSn#9Ly{DrmTF2FcAE6)G4g2|4@T2l0ui!_Sag@At_z~Moygyio{#oMsFrLQ)Kgzr|GAsF='
    'ng1$w^Pun}`EiHvqhM~H3x1TjJ!4+a(fE;AAG_r?@uQJrcCiOPTKMg;z>oZx+h?`~{D>dB13x;wDSjk|_W<yti^m8*I=xT)=;T1}'
    'x~8kxi5@%K@FRcoAH=1_!Nmyg7eB&(6Ml3N{HW}dClh|Oeoe=F*Z7e*llla8GiZ1Oesq2aKZ1dXp^X~;i~GTk#MlRZbhg5eE@%9R'
    '9X;yz8V5QCKN5c**9D8{_o+Ks<45pgJSOjO8-'
    '64QnGbp!_)+n6&(PAp<&j4o>3GZ3E6MrYiyxtty0(%*o%288M;F`hBfQ|;n7>Ts-UL5V(^~o>wMjeiBl2j%kK|K!|M=iX@CW!&W)'
    'SVbk1luMM~#8Vt5#bX{K!19lIxcv7QGWcV*kO9#0b~1_9O74E3x_O;74Ky6Ml5L2R}L=_|f^mkGh_N&nfm=dTJMbbiM~aIve;=$N'
    '%Uz_2Q-'
    'LX8dS5ubIVy#`W=yACYbPVcEYC>uaBQ3x0HQ+xSspUg8$p@FTPnV?wJs9~<})dOm3U2#%m%nYn3d;NJA6H!b*4@ymiAiI*OMA1yU'
    '8^Ge;q0sQD<g&$qaK6daUy3m=&v+6h2_z}Eh!jDe3;71qN!H<d;7yRf$ANtTi{HXk8`_nY6z3Mo=Yxdk0{Aeq^<~7&Sq^DKtKhjS'
    'uwQl~-|F+>rc#A%m@gqEbBz_eC>ZbUSv$TO9xu!$-'
    'kzSK!ANKy1PG}n9?_eA&{Ah!AbKTW3wM3~w3Vs9whdY!EZyD>J(39OwzBmiFfFGS+13&8T#>-'
    ';hXo|PU8++?o_`bo9Mt|T1KceG?Tv}#cTmwH^&hlL6l^U73jxBtL$MA*w5}$^R)bD-P>ipafesmW6$Qgqlk?-'
    'iR2S4&%Jtubb<mlXjHGag-_FVn1>jq0UFS(X-XiBz(50-'
    'e&j34cqZ*(Mnl(>+3r)387h~Xx$sBJ8@&tx(kx(`2MzZRc$UrnDm;YV$+=;7?V+T+xo4E*SP;76xx{77Hb2|qfY@gsT+PBHqc^_<'
    '_2e)OZ~>7j$~gCC()`d<b=%Gx#4=n#H{@A%OAA*=CLr@qFI$R4<h8PSLEBfW3<;q-'
    '`@&l*1(HuBO>bQgZ)wfvo;OZS#XKX&IDKeFHKcGt}o<^PoK>lvxr@FVsiTNT|sIwy0@(INaObx5Np-Q_1g`N^a3Bl}l8eh@!mvt%'
    '~bJa<9t0Di>ZGLx47QulH!e)J&gkM2C#@gw^CF~pDNT(y%e_|d&5GyWkLJNVJ)?-2Z`ZMpEugdg3s{^-'
    'sg{OHL_!{$3Rn&CV5zQT_#C;aIA0Dknpt^Vlb8u*bo)h_(#zUq%khBkgw_SS9VM~wk_&b)H9MjoH~)Tj2!bN5q!bO=9kwo`vpw&f'
    'Z>y7l^_vWI5;sN?q6#gF)_k0X9`KI2EDM?lZ3--REIc;|iNN6BB@h99x{u8AL=JZSugEORbHKll;*T(2}ZX7R#Of5b<h;?f84Bi9'
    'H=;p?sOBXqz=+wdcCH}(M@!;4e>(Mj1{C&7=<(Px{Ja|l23yR&{%{0I&4teJ27>W|<7_|G*5KN@jReW;GYkMu!AhtehZXjlEwon8'
    '2mxiIy*V{wlKKiXA)bieo!o^+OnJ>Gr^zlk3;YJNBBkMye>_|csiKbmIW?!%9I5AR1OSYy`DvG2Ke2tN{64Spp5F8EQ&|AX~MWKD'
    'b)_z@dKKWj5%(gS+Jk1p>6KkB%c-'
    'gdj{kH##i)*oirz>ms5I~{$ax>w|ot?kp|m22Whm;3M|{e|((j32=Y^`Jc#Kaw;0u6Mnw^T1(s6Ml5Q1wZO*E?z$dKiXM;B=>c$K'
    'Y|a7WpBfe*hky&BXOSKN93UEs^@3?h~0X*u0MhuT@yd*erarwZS_a+BYFy+<nso8lv;*+Gkzq7wgW%9@A@OXsPwOaAL$20CX*p@a'
    'P|Dshn0*-{gIis`uON8C_a}NodZ8=UPVK+k~b>P7yXXJkCyr)aXIl-'
    'a(h?((TpFJ9k3xoCj7|9i+OZU+mfeUKbHEV9r)3;>yMnflKp2hex#>ho&E0rmwJF*^+#xjPO##EACY?<+qq8tQSm^}QgQF()0pwT'
    ';78?iG)6+s@4}B@OEZ3?cU|36%OA3-_?C{o4t{jM^+&x@cVy4j^+!kGN2dcnI+^N^P6mE-HrF4K>Fg_VZ}bN3b0zi}{HSPqlHQ0P'
    '``E{tc4hAzg&(Pn5XTq$gbUnu{ZVFFXC10Px=;LQXZ=yxggfygy{_OTU;gr!&HtEf-'
    'j3n!!jFcI>HNU@{@_RF2k@iYu0J~6fghdRB7StR{>W#f{)k_|zAgW{YbfaV)E~JPbJ@(?GQU#Kv>88w^9Mi5yzltbw^4sI^;GL~S'
    'o)@Ckf9wrmfcmq-'
    'v)kkdL({yvaUZWowVRbuE~9Qk65}#v>aGUpPS%E>W^mpNUu!qWt*ml+AZKmT}L(JM=*mKKN@m=#*b2e)H04u&mXoX{OEEEe$+Y{e'
    'uU>-3mUk$ef3B6eAkr7Cz3Nl&m<orH7{hcYp&1jeu8G7tnj0=x&COzkJi2GZc=~bT(L7szBhjKPyh5!2k|4e-'
    '46VSAAYhAKT@}YUi<2goOAvTn?_Co`gskX2X4d$wfxS0cir^eKK!U;@CJUA`lFlTNA9C!-'
    'N}e|;W0kbUi@g}X0@GiUHr%%)fv82f8?IwRV)0c&k`PS)`ktz_pdLlIm6;e<(GAhXwGD0So(81pQDG<yqYKUX(y-'
    '3$H;TyCASv;6$j(n>+6zO6k3h=+!7b$KUnFt&fasL6N^gU=KLOeIx`pMnIP!vjEbj_>1d)it$IK+wAp=@-'
    's$>s=!ebjp%>6C{m_$RKyH(P>}h#rMR)rTr#+css+ln>M{;MJS^Nk+#EsHxS?o%0A+e~;WDv8m#8k&DhK_5we|(0YoJX-IpXWKBC'
    '+@?K;Nx2U&!@6{x4-'
    '!#>Kpt$>KYc_W;goZ$e#}G)AM%m+L&$My)*{y+vkJ+iB7f9PMjuodf86#Tjn*#M9x0<xz8;)T=)flh!czFiSMC-KIw@C;}1W0ij4'
    '6d3w>5Ja#rL(>7m(uBFP&4Fz7_~oEk@Q7cnex7jleDlh0eSi0#}l4E^v+w)LZ!me`iLg~eOl`$J65p0R!DLw(crayIXQ@98^A4t9'
    '@OHl=f#*}9_-'
    'f76a#AUD(fmcH70zTBHLRrhC4me`FNPuP{1&6owzwNQT87J6IjpReCJUgp!e4{;oGhGE%el$Q+bc@w2O>`%*Nwhr5czINT@PVopI'
    'x^wXA^&PVs=Y}2G_sm~5KNM}rb-EL6=m7uYA9|iVgsIbc7M&<gK}L&p$w7GC>t5HGM_vD7L&r{&r&G2#y?Zj%wI%nh`33)!EpTGi'
    'g*caZD!bb~nSrQ}wc26+s%sfo>3uKQLh823c6uLe=%c#Vo>ibvu6~B%MtW(}h2hsM@h-'
    'WmVh{Gkb$V{h73f?9`PG?4IWRPF#;*BsuGl_uK7wnKmG+ekD}E+NW*o229a@Peky&i9QCAEj?U@PeKKwAnxHgu(fltw8cpN?A6Ot'
    'S0vFCc?$FQ-zCOs$O2gVn~kFn(~yr4(BxY@{IKQpgm%wFsjdjqY|mi{Hr#1zF~J<q>zJ;SbIo8qainPD55{b(;;lWV49z2>2Z9y*'
    '!%4c*uYc#eJ|m)K5vpTIcSrE0}}7d_<Mh)dx+IoI-9oDFBk5`#ixGnI;-mwGOU7dba#?#_@tVB{FtEl%h<y=Tne+qtqgbYWr-'
    '_!2$zjS21MM=Lo%>Zs9=?2zAQUwocDsz)=bPX`9oxVroG8a&FkEIVf5Il2y?WlpPJPI}|ZUuF~M`uOeQ7-'
    'YElAo9b_BPl(7a?_fSd8y?eeWd#A=)Fz{nw4BSgATYHGfbA1Sev~pzHQp1wmvcH&}?2lORNA5>#_9#S>asSXR?pqCr?FAhdoVx5I'
    'hO3<kG<b{GM63rDs}KPv??PbS6iMEZs6s%DkuB%mvt``#17c$aM4U*}nW8x&tjN@q8<CFZS}ha)!x6{5R*W*pKOait#P;kV_UhJ8'
    'dtpq0pC~RytjroUHD1ML)uj#w@FSa|Zd`Y{7kV8{5``NysG=Cm~eSoo;(AU7ts1qwJq;d@E*!&ssLowP=UmoKrH8PKO(<X=mZjoM'
    'Zeq%|^|9<+cUP!eejnnd&p?spd0t;>*VB{UZ}2?-'
    'MIRLpGN>zB;cP=S<91+=zcze9$&w`Cpe}>Gr&II{xqYqk0LSp|+>=CA*bxz4mWTraoP5<ESYp|9=D1<cpeZFrQyCo&3aaIj`)MfB'
    '1)gu>Z|};@F{CmNOndmj0dThX!H*>QTt*;m?b8w2q=blcSYBymSh>k9l!@U1B7#gQ92ag8HnsLu<d<b}QeIT^0Pj?WTz)^o%%n+w'
    '*1r@MAi5zluk<|4}-'
    'AqrXD!*@DBdy+)6_CGW`+Gk5;*(C9VR`m1Qy_zN5iAEIsWrmUQAHjn=PGyU)n9TFaeo7Nt5KRahM`xaYbTf8Z@#nkI&jW2D?a4-'
    'A6Yun3KY)tGx?MKVivZFgzR`zgz20SA&hs`CHx7NA#*)^FFjSlz?Mk03Mj1@gv|B2(ForV9#ETm<zrO_L0T<<LZ29DGJXCIC}jZG'
    '{2$ZiVV&?&y$919Ijl*c)~Ox`5s?CiiSJkOpSags}M9J5V6``OR-'
    'b&v;qD)}v9$7ob~tLIM18z5(X;TL{EUT@zAKa);npTrhKJKxD3grnn|fBUz8>-'
    '&eP%9CPqln>mt0~^Zg(APD1<mbVo#IZ)7yzWc4o(JK6*jDs3TFZ4tqu8L~v(PPT7v`3@^8D!agPv_i(c5fa=iT)><8b$)&1Km*mv'
    'of%=}&*UeOC7nT*!AiljI7T`8~c{>}&i-'
    ')`&NvS!Or*yRN6PI5L;q^Z9g2W<N~*dzRU1W+AET;!n+SOZ+$ZYqr7rd?&vxG59qd*R-'
    '2s^6Qluo9s^ao!l>egnP}xGkC~r@RT!<o_3LC?5iyA2`-'
    'x0Ke~B8+}FA0$B{*1i{h*F&8R`(KevyUoS@8B_xG3q)~^@q;HSUrWiM+yg#RlZoO$>B0Wz@8SJ&*3i)fTNCG*Nz-'
    'o}&GKKwG6(3r8@&&3a$c?ccQ42^=rSzZ&_uwJo4izoZ6s}&G;M+c9tnZ7Znlz&MEIH%}_zQb>B+R@AYF8cMHMLBnHqp}N@_-'
    ';Ped-+xHdhvXFlAexuG%<(FhneTXM21Eu&Dhb*uQSg^E+$W5e%*}EMgF6UHRDQax<%*e1qj<HpQ^7f@od*m?-'
    'Va}42T_TE~k8tV3Wa&{f@`Tys~W@D}s5d%U7R4f73DKWAutxOz}EjxNW`E_-Dq;Jd0<IWvuaxdHzmv47bsG<h@>bZe9O1%YZdLip'
    'HT`{jc#k^DJFMFmKoGJeQv77@BhkFGD}~PPWn=XfWpJwcaqlOkNq>7{-'
    'Kt@QK)mqaSkHHY5K*+_B?3{5>%s{7t@+C2}FG@NZ;Aa0|4ym+QGl>0g(%rg!*z=JR=tbJR3h_Y*`zHn_RjaA`ReXb@Wt_Jg;bX>l'
    'eorjf7Py2E|4Ih;MOAJ|ks_voXKcAhJ&R~(!S6cdq`#MU11nD%A(cjzbv%Z@D{plKVQI=W@_5J)e(<<W8tmi?R7g5lYN{GNSCZCL'
    'Q4{O&QY&%Sw%PvJ3p#D^r`#WJ4x%xAWp?i$E(IF>y{bGaQbb{N5!-_&sr_i2vlOb>R*i1&4$Y_t<EhpCj0xSSVfflSetz)V;*-'
    '|REIRNuMG70Vh}M%%Olliiq;TD0hS(Cjw(O2s#geT*98`^Jqj?*mo=yO7hI9)2T7dFj29nPisV#c0Se{xm;P|Lb5%^IBt_c`i%eF'
    't{@rLZ&$XAN=44yXM_~51+2<bSK(nu21J3im~&f#;mGcae(BlI{)`}(SzSFb_nYc*Ot#Fhg^=6eV{Alk0+m8-'
    'UF=L_lqf`kJ)bcNnc5EOty)YnQv%^Zfefa*Z<Vg!&ZDZY{k8#r(z!cZ_Ya(Gt!s(HS!OpDF*}3kxk?ZzMSR<F8y=liNNl~ujH2>;'
    '1_ay@mqbjd>t}4SQ<K5@HA%xpSWNAfes_@Gks6G&pynA?J@dfb>9nqEg4LoMNYDZQ~xIqfPF#l!8YhsvjxfZ_-'
    'N!0`DKw&&M=In?Dt-'
    '<T{u;p=a$K66&#zq5wpjC(_A{U7Lx<%jQ1YXMFX?j;3N1T+{|8&S=6bGZyv0@>KG#WvmZi_p$o;*o3F`UzPuQXdv`B<BKna3MQ71'
    'T7Fw}+*pF;xwjvvm%@co}uA*D{RAj09#y`QZqp$D}8Jm2KSs&Kw@AY@`g2+HN2Hi$Su{B3N`C?0`sTmk%+mCb?Y+0^-'
    'XvQuQ`(tB{{H6X|Z!39;!{7J0?Vr`(tyA3J6nDS4>Ege!sbkY5cIo<KKe=Z*hn{ra?9XRD^O?pn_{DgKUXpW}*w%VQmnH^_Mn2cQ'
    '*c&vDuQu@Y?v24_f^{Sp0%kPoLs}N88<wvx#wRZcorl~(uZ}_SAGXkG8&<LN|9m;VTY8db#gFqp-xFIqzD#Bn1)sySiIwPkB36Qa'
    '@_x`R@%%k&$%n<GXpZ*yFuumf=e!twf;tC`e$$U9Go6M`@AxXZiDlOL>wPs#_Z6>rMdyMJe=0eoEpuE4>={mBZoE8vF~7{Tc9!LV'
    'l85Al8LIM)Vb$_s@sHk6?w76S9I_)OeCP_FnthEQ#?0aNThP<_<Rhb@&l4j(L_f46OW9sx1<o(}Ilr-C;Vbo-Ex*|XbRs@uOX4y5'
    'OE2(;9(t(p>w$4*bzT&C2a}=?O6SnWWawj36PY;uhzF9h9phrxjhz2w4qN<2^ds}o&pnV~(I1ES5B<ml@o2fs@%v(LmJDfK=`1>%'
    '^dkLHwAA;jZBud}G7N9QSH<2-?{C9-`u;{u&QUaB<CVQ|6HI9veb4k)|LkW!+ximi@R9S&cMvlP?bh-'
    '8HT`Ct<NP}N^sv1UV^gOgu8m&o1u@#<H8G8rkz)>g$8deO{MA)X!j)R0kyF%jm({8{`^6t(m-'
    'J2JMdSqiEjO9GV7HW=!=Gr|!Q38p;J^Sn|Al?XE{5B~ok~8p?wa~z&b-'
    '+<s{9sug}p)cqX8QS{n#yQ`px({`q2+~j7}EE#DB?^M8BeA_heT;UA9H%C8lnGjN!Ah5uNv;<J(qpZ=-MD$%q-'
    'ZomVyq8g|W*oNPEcJ7Uxo!G@bw<R=-#Po>Z4do>d){d0F<NU5J8kIlkn-<;JwuzeRCsm@K;b<DCb7>@gQzs|210-'
    'sF|YxKyxX8uDze8iS4diR`OpD}Vy^|$DH6+KE~|B-KK#vh?utju^Pm(f+e0H0SZSsa2-_>OnHqid@^_qor_{fp-'
    'w+if4p^Wl%)yLYc2hrZ~#?&)=R$F+2B+|+ZguW{s4Hr?v%w|=FAM{Q*He;U1c`s~KPCb#PM&R2AvBMY;}-'
    ')+Cp7l}Eehd70^PX`bA+55tNW)mb2C9}4z%rmzJ7T><{s4v*I?oQZaV;;3<d+R-Re9qbMd+cjIQ(wW;(9P@w_hG-ywbu*7UZuAYd'
    'g2}TNDk7!^0eqdbGto{kLDHo#v`3OVh26zogae-@gLi;&Q9|ay6LUN4xD2MnNyxw@Yd*AxAa^}Un_g<+SzRSf8~D7Cmr%A^V4QJ-'
    '(AyG3|MZw_{tmK_{OCsPA(AH>>R)5HLp1zb#u*c_7Z=(hIw8+pP%kbzOXX`+Y?tIk32um%Jw_nq90&2pZLTlk`sTCUM}cHhK{~Se'
    'I`Sj!DAZ>?Y7Zx*RtRAmAIO{8a6Ort@G(&;A~3ujB;4ixUtXWB1i6%!_J9#anW3_qpqJZS4bV4_^7>dPVt=mLc8=JLrXkCZzKlHZ'
    'sc3lPs=KNh5wS5Z3TB47-;A3M*q^`bnU>^Q)||-nGp-_^O`tT9%ufW>6E{B^{jKId@gxX=b-tLuRxx-MzYyCaYlyU**uYcT8XdI2'
    'l#35cGJw6K}U32_isZ>wDURfoAHUbYn@59;^GU_&4~#ora!O+F&sHoP5;Dn;htzm_mH>r;>bx@;=C*TXoIGq<-'
    'BH^qMdv2JHB?m?gbr39(zBJwx0LhiP4XKfaiH1dFBzFviz+_+uZAJ?u+Mt_9(Qo&}qb!I)+nzXzOG5ZXeloi6huIm`d3LoiD5B={'
    '(!s=g}=<u<GcXfA^I*`#x-'
    'AT^BR(qYe6o#@5_Bkq%6p3@>>ueH6V8FMDnJDSFKEy7ai4X*RFvH46@w8qU}hbw1Odx%KpnUnU;L5Bu_$zuZ1QJF{$qmWT9(#b$;'
    'l!T$BwB`47|`>+i^I#dsH2tQiqe#~`A=so3%^gf_(WbG^?@DMtohu^JP=H(ov_KM7(=0&tmWxl)nLgRVXk^3Ee{JJiQ56d5~73`>'
    'OZ}A(kL+6+8PX;BPGtWPo*If6K{kmWL$lqD(Jy_>Utns>8zM#83$$UCCo@@2@G&iDsd%8&<&BOxSD|^M`;J@xyARn23BR@`U&5Rq'
    'tpN9X}F&)cu<N5Ya*o<_uM+@!QiLo<1T4cW!-'
    'Jf*`Kk|F_VvX$uqt3o$Z|42+T>ftl*%GdsKExkBBY6U2Moi~~qTf&c<WF{<2ER@2B)ZT8Mc?k-'
    'zz0V^KWc2`Z`ecM=Ni)&IDHTCg6oRjNN&}z-?}~u4}at%A4x7%$6~~_#An1DJX-'
    '2x;S<h@AF&v*5jLAg{&nqX`y6~QwdZn);LqaEY7XRkvUy;D_Vn|g|9oTodPwL6{qmQ;{H%09+rD_0%$#LnbXxLw+>iUh*XX&%L_-'
    'U_?ehl4w}G?T<B{93<YV}3pA`%w`EAyi>BEngm&lHFy~}fO8}T|Z0k{@y0@lH&&8%B7J+#5|_|13Gi+r55zac)shNExUC3&>iD*i'
    'w9dh0qWe1q;q-<Ip?H8sbCvyx{rW>56_B`XrMPJg+?NYP`KF=*s{=oVTBr;cxz?+xwrmBushE3vim*Oy#AdA4$Q*}Lc~-'
    'l>OyGvs?lTyv{$$5%*g0~;dwZdu7Ym>=g{rI9lf+pnK<59x2SO>X9K^qgCIFvT`RE3ZKh=M=qCPfA84_bRofUXRYBzs4em)6=Q+O'
    'vkarg4KGVU!9xuVDA}(WkYq2-H4T3tb23dGc-yLM)a<02(No|Pnl_->-5^3kvYFG`7x<c&x#G{eY4)r`HWrQv!kbiCy}4d2Rg-'
    '$afavInB+yEn>`{2y=KVQrrnTt?84?Ld?)|S8HJsdE!5Z&n|H$1ml$tyR$W*6J0$Nve3QCPG#!0iHWrK?%~J>EwV`upGSvw*&62w'
    '{*Zya&Y2F_moM||pPkct#(UHkHOdnpdFLOchrT<4ig?D|Q8g8*<SfgAUdI9Ev2lemAYso=NJxOYRQm-'
    ';%H=W~D`nzk<9(w2@vasbO+4!yB`mOPCuPphEC2RY2>@RVxpZ(dN?L2ikqih9uiufbG3Qq=G8gYxI7lrEyrnJWBX1?@0I<OPi5BQ'
    'PYhNf0*Fm{pW(LZ*u&y*Yg-uJ$@@maLv%LmI*<DcG(con?{zR)=w@=;(zbngx7WbOz1XnO>$#khlIiP^bdGIm>Bj9kGl(FOP_XTq'
    '6emx;m5%Q?o2>?FK5^R9i-Zv*C&e3AO;-UEIwb3^^qQXiMR1o-'
    'Ct&|vhSTIi8_+}p;NluL_Mizz#c?q$Tg`rgsdbLfXo?B4ilS<bifmtNWN9XyWO&9>QKN9z08VB&3RqwTL=ADK^3cG$(#m+jzv$Rl'
    '9~I*)7~He7v1&l!==4U-@J;^Z-'
    'O92+k0hg}4N)`v5nr>0n*hsRN4b6uLkl{)r=cFAeRlZgrO#pcCF@qB!P<OutlY?MdEcGKg7?JBmWPlvvI_7E=eLqGIGxsLdf_vW('
    '%+i~7s``XtoSOmGr&gU=6IbkoPf1KJ<G;{7Pu_AlLzZ&*M=d8%(P#;#Z@ZR9l)8ePj`$FeBw_WEfmjpJgj;#1#qsJ0^i`<2;s!=Y'
    'P+GjEPIdw(o$Jaui(9Y}d9lk^_@-Q?-'
    'L$iHg)OxIxAJsZ`=md7}$*5aR{?)xv2TBHXKTh`!6O$w4%#R+%9dnQUGR=MLekwi#7AGH6uDf`;9v^Rd)0;Xz^2dMt$FY+)V)-'
    'L4u4}$u`qG!SZYg?ots+|MOJBCu28OBs3LkTdhcB4YTq{mCk#%AOXfyh0H4f)II=|>j|Dq>8q`%Z&)c1GH5#I$bz|(9!IS4Q`*RQ'
    '6%?85#$z0~CXsyU!%)y<3PeBldUSobZyQcojK@g*;LN#`EuA4onpyK3de?3QhKihM|)dw12>?QZ%7%(!#;h^<S=ywv5US6pJe@%7'
    'k0UPE`F6WaM*tTc6qXojwy_ZXQePUrpTmOMbuC;w0WwSD}+2R?8<_5ErLvp#FveabIx?DFfs{_D5l8w+kE$1FWk$YXxnF4`5H?~V'
    'CfYmDmj>%Q*mLbuK($0u|o9Xsl-'
    '+c$P^GY*mEoH)yPFEJ2j6OR<{v|lA|f{&eV`Xsa)Sj+hw_w;*aNfgc01>wDmk=wHPVQLe1(9kt6*xTrzeD?<VR(z~rZT5HJJ-viR'
    '-a~(f9GTn~TA+(FHDdYUi)95Xv(R|NMHdW2eTTk)da2O~crv*|bDzEu*SvyJTE2r%px2pmTc2|=`XqGxo!phzfrhR#vw22e?ltxX'
    'BTBD;y)=V0!O4T!4S9Gm>JiB5o-0)PyzL2l8LSAO1^XQs(#{z-'
    '?n5rWd!=8U_4vEuPHYZ%m)s?}3SxPgGanf@*Kf={z!JyuJ^b0CI~%d}fWKXX?`Dh3t0Pwv`%J8E^s4RquJeC7^;kI_=UXhQWuIKz'
    'RqjRRJS{yZ#p_@Wd;tC#nHE3MSqZL$ZuZi1yJ+VzF$g>tn`G2`iJf(>S=kg_oAalC`lnqd<KECMao@S;SJoWg9r~$hP@iEAQePh$'
    'l96cW^T>|ktp&5rcetL!G}!+1JK1T!U9)^_zoU0%x7lCvi%cYU$ZzMy=VTT{Xa*lahu|c~&R5EeZ8S@Nvh)xm_t-'
    '^z3iTiKqPje1Eq?Dh-oCFk22YU_`skD&%9if$=Odx5J;bl%L(#G6iw`1u;wLA!F}={eCvk<?vhhWIcYM>)gK@#<gTv*FZo`viKAY'
    '(l8RObVjqu{r+H<rs$4~yA+$QwXSCs!ve<Ti#XXn0Mhwvk7#8&mmYT4sH*+8C02Y5X`XWztTNDrv=B1udy^?zGx4makSg+{^RB4^'
    'Rk3WhYVc{Y_5dnLG&{g%@-a)-`G&1KsIa(M6_|G#{Oj(_OQDi48P9{5r7N@o4!@eqE5-'
    'sq`^ud}S5ud|0gGrx;JDDGaqeD4MMYHw$r##4!<XU#K4(kE~o|D1aW&TCcQy`c+79RDKysK^#M9L}WNK=&=DRZYLVy!6{5kIBB0d'
    'EKu`yqga#29#bD>HzpxeupRdeHVT-'
    '<3?nWI#2zy^qA9AI(X5*L;Lge*Rsc{uO(|zYm__*f2UVwaHFi?MmY~NmKr>Djax^q&nwu6*Qj&Q=SnYexvFezxp?X-'
    '@SJ?xQTL0E-BV%2=r6|HnXXk4E2!5ly)w(L<5TtXFd)9Z-l6<6`KWwbF#s_xIlkrdpVjwu{WD%88_3XYHEZjcN$Zt5&a7>-'
    'g64J1XKee-IW9e4+qTySE3scAUfj7e;_+xCHf7cV{W<)K&UqTMygLR+eyUyJ=a&7~xEWbWPm*Wp&6T`2@{C=v#x&OTr@=IWk$F$%'
    '@cE2gJ!NM+WF24Lx7Kx_^Zce6gPUq$78=%bv7b8L0ee(0CQb_5oM!l(z3+YRYa9)qJ>wbAz-'
    'v82jGP#~eHMFc<UcKSy72+se=x(yz4=TA^T(@XSFjEAbG@@{3??+s=1UD`YO{lfL>EP`AH%b28Yd>b?%`@K8J>b`pq=xHer)T~8H'
    '<fubZXmG%+zd%dG^fcfwa`+TfsAeE6nv&spCxzwVt2)SXt!vROj3MPvlmMS&g3G-'
    '2;n06yMJ5rO+lh2d*zOz@l5`n)mQ*{H$3Y&A+en9YVixU+OIuz9S!<O~3Q)#;msHCv};8+RQWKyWy+Y8#y~UW8u9q%d2BZr8l|{p'
    ';|!pr`X}1S?~w@Ud{fBm?4`&+=@<Q)5^u8S6rLx3HA{h;?LC91eZ#Gk(o|2->p_-'
    'Y4Z#{^z%2YMl3eH;p~;~7Tb<Z=DX9IAaN7@p^HCyt^}Pm`DJ%*Fa!S9V)f=tsJGCglJ1wAJ^ERnuX@9G-'
    'x|yRlCzvVg%vHEUh|@#;k(a&{`0#=fh}M^$eYY1T+L7Dcxu^@@S2lbpwG!3o?Ab^?RD42nZ$tW%#ll78;CZeCu}b~6Izlvp<}Iu?'
    '=1Wx|Kg=DeQA1&FFm)>U(KU@E&Z{)UhMn8S-'
    'Ug$UEOsK@w!?Ex*VQKra0el7xt9;1$}bF=Ed^$+}%gp^bxxOT{n1EZounb|N8Df$#$K46%T%F`z`eIBc6<h#Q@M+Y?Ti(@>zS{hI'
    '=zRZ3i!GJP-'
    'R&!%{R_un+ZZYE#A9)oZg=)ugJ&E_=22k&Vwzg*n?(J^l1zAWQWwB1_fclBeeN7R{IafvcGp^6S6;>pe$G4@dRZ>TqCtbG^1as%`'
    'td4O=q*ldr}`8@6}r3bqS-j(jLPxoJnHk$Lon7}TgU#pC<VRBHS>2kQ-QctiW!W2VTR@&E4m!Ox(R@wRI*ALCbl^;df?jv7QcMtX'
    '3=f$$((oo&u8^`7YT<c#rI>%NwnkI|F9A6*lBUOqZ32G77)ipJ=-'
    '(NpgguXsh{Qu<}Er|971LnIaw`6mvDN9~U~=k$1WZFG`49PvT+3O@}k%?_aB%(ocx`A&mX%Tq(Q=pa3P#45h|o4<Lf<4<48<iiCA'
    'DtX<rz}0Gs<Cw+6hO9HtJ$PZ4`Zql7X-'
    '_*J^E1vzuKmRd>*(*HclAc(%kn|_?o;hiV<Kh^PJ7>d#pOrf6?^3Sokc!CYO&M9dDw=XFJ0H+EcH228(H6%Sh8zqT;68}J7D+d16'
    '*gO`;D1Jtrl8*C4C!5K1Ih}ie@wYcE*;ACmS<@Q@rCH@3=IZ*_kcdy}z&aMn1#7_%wO251*Rxqy>j7`P%eAGqQ@mjYhFE);VuvVE'
    'hpK#6H$D1(uB;i_e!lGB#1pvDlNk4d;2xK0jvN9k^O>qbskO^Y`?OWm~B0_`nA~0Ke-xaWUArriov<npNX9{T-'
    '!?cG2y0!r{6fBRkM}OD}$UHU0OJ*S=nJ5BB8Rn5RK*@k5G+c&G7=VHbCt)91^B6>k|c4|Xp1HqoW;ujIg7_jYlM>$1*v%aYPpSNO'
    'Wl(dm3nA9>`FB`+*7A9B=viXn;vt}&&7D{agyNq+;h<YUxlb&P;-'
    'tM9n8pISk&N59)Ac0C?6OBr3oZ;}U}`U9^Qzgf?C!UMym?s>wiy1#4F&1{d*rS^5k@w(QPO@!C<!WHKl{l=FZv{83-p6f-'
    'w#HpwHijC){wdAik(|X6!mvn*JyQ0xDn>Djx{Eq+RlZykQ85*YNSK=N%Gj^uueV4fXbWYDE+u@A8K5}dJ;%{QyANtUT+CQ=f=H#e'
    'fn(cYIQ|}=?74esxSN?>vhS$U@M(lryXM5a*hwNEPtPvgAg<>)EI~tlbNMDY5tHEWuPg43H(<{lho#Vcduk?-'
    'YNX}+@G>!c0?rFyVUi-6Xss^rf+L<#ko?ByZ%PcPU;#v|r7q3lxhweqkF<a_<U>vD`TIxmCn8-'
    '2oOYDdq@%eS8yWX5GE?G$DExCw^=b)v&GwgD+E!fy2M`6)Xb6jNh$wSZNZ?fUilXmP)UyJ)igV+k_?|t#L@x0Fx19le3<<vfU-'
    '{`~F{7?R*?#l{Jas+)g&hZ*Mai)?-X(f(c*W7a&<d2oF#OI##UYcLg#yNpKnXi<&2f-'
    '$jM;MGQ`OIrwmfY9KqtGq+V02b$NAZ;vjK=c6U@xhQ89nEhTzxe2ckng5=KhmwuuWIYxd`)G_k&EGbQa8H^fY59_v|1vlvm{%VGh'
    'CO@B@2B9*r8(Vb}EYnX{Bymbq78W)2503N948Ao067ZkRpsT;z53BfXOohl<@6nX~RUI<Ia0T<8C<_3i5YOPx(-'
    '3b1?OJA4?u;N&R`e_SnndM7lk(Ozx{8oujY?~*UZZfpKYy*3_6Zr412Dl5Gzf{&&Sd|Q28){IB{J%7*jVZo6O;YaH}gEQur{K@2('
    'Z;MsW_)+a)=NtNg;f|RMtt-cjw<i^TG}l5r2>j^Yy?dS4A#U`;Km5a)3)+5B`A@AU(au6M_>tVyefW_*5MxcP$Ny&hNUu6P$oAsv'
    '>&qd=x(`1Jh7%m;vBr<mTYBy<`$WKxicW2J=?|d4qH8_|Kgu4?vgfhHkAfkgzx#b6;75E#xyWp+;74edb2<0GeLV4_7ryX?3x4#e'
    'PkpL;wLaeXk<SjD(jP8oB<B-'
    '8u*Q!{7Cxcyqp$nAuj|^CCnA2NFMt_qdWilHz>h9x{3t!;6VJOYev}wH`pem$@uRY<kHL@b+!Q|&dzbH|k0t$YuB;i14+=jrQ&o+'
    'FI&C&>>J!sTL9e6h;zxQ>(bbPNe&joXA9;iysUyA)exxUl1-'
    'H}BOux}Jex$bMSp3KwQ2xPn@gs31ex}&MZQw_GTJt%!;YZ}uj33Ec!h>v1w&r#4qx5-'
    'ZPh4JJw(Rp+Gk#R(?FxS6`Z9CRXQwXS8IDac?3XL}QQ3FRo6bG_NZ$edjO0Sn!NHFndg!4I{K(nU7am^ZUV|TbZpM$;ZmHKyTqO9'
    'B+UprVvWI%juJI#%nvTJb$mMI`N9IG`H-02;T7K|?AB{dz3w|_w{yu+r)iu_4_BkXc_|h;tzO-vz<3}Y2_ToqCjRt<ybz8xY)RDo'
    'D#thP(_)+ouwecf!WHRUZe()o*hRjs&mKx(Vex%k<uKDm?u8kkno*#uDjlLQSegr>V_rzP{E5VP-'
    '7CZ_+DxK8l%o!EO;QKsA_|bXrBQeTR=e556#}z+%_q*SnUWo_sBl3v-'
    '@4jdJD0NAX5q{La(>=kD)SeIgD0z$5#*f4_?}u(<o_Evbt6%-'
    '<27V;(dmDb_UeXhcJbJ9~qsYNEek4y{F8RQZ&ToPr)pvED*PNxYIa)3p!jItfu2FATdr)>1n|CLEgtszViq59@#VQ8w_N2p)$QZW'
    'h=%K{+>p0jp{HWwH>}V%`q-'
    'Wyb?>>uSvupgwcRDkfp=1B?{Qm^}i0om*rB}Gm7&9RIe$itWeq_&l7Ms9XNNt5!?HWIF4KvN2?D)})A)r_AqtrSDGunk8!QA2(d7'
    'dmo+sKMr#E-7bUVEb8N5LHC-elLskLEelIV1BuKS}VT%f}l(n(?6-'
    'J9+^4QTtpLEJz$Wf5#WI;3DE7{5yI@UVzzF?|ILAnm*}4Hupze$HwPbdh5AvGk%dhPTV-'
    'X%YvQEuMcjS831{1?x}SMn~JVWta;lEyKVT<s0nSF1xuT0msp^BB)D4X$i_R&qO&i_DM^moe7))I6?`c7<+<!-'
    '@J75g<BpM;V`j@jYww-$x4A#djGYA+&OWW_JI_?vh9j-<xNS6_{=d*KG{kG-'
    'F>D5LAbjRbj(La6++Q|maI(mW)Pi_EHIi#xl6%W*>3jVI<igPD<_`0jeI8qHo-eN!GW}x2In{GIbK&LGTBPPFaxii(7=3z+c~AB='
    'a&H%Yv<(MI{<tOP2D=pF*0WFUCq0+gjmP+dv&_x)*%yzQIhFfS&+6XIniW?OlM<g%3-;8fKJ_~I$37gS?L#vg&d<-'
    'gXa2AK+OIVRLXP8W=iWWo`^;z!1~SW&$dF)4+px^3=Uw}}&M3e4d%yR4^=xUG>|Ex2#(oQpvY#WDX|c&*ANWYkr+66q=Y}!$L+eK'
    'U#4K{iJZm%c$PU+^{3SlI-'
    ')HPI@^r0(M;xYOiofzJzXHE#{gc_J_91f2`=?%r8+eQOm6`GCGOmf69ZR2+TUZC@)R^mTZh$x^Ufed532lSB4qezj7+H=!;pOxL_'
    'n6+8c%9#-'
    'rdZtkZEt(q>6RW{$K1!!_pK+Dyby6@zOsH{x4@&v&~=dqW2U!U>9*}Mmmod**dJ`&<Upm5VEVbMOIOS0oNwtNcaU#JP1my5WNhpu'
    'a@HI(_{BTl`OY)Flg%yt>}NkK-'
    '$BiM_eT^<RS(F{l#{C`6pV?D;B&}Rk3aGwKQix8%k(k3#yp$uKRj@(eS3Kw+0t=Ic5doQ=UMXlUln~D%T<5=q8Gg=ec|?9L*t*~@'
    'E`feN6d&^umxBFJ6m5Y@&_-'
    'QIl|5*2lPLN$Jq1C3bNQw;!t|`79AT;q_^p6KBPT16R><BvESvop8f1+oBP!@IP{iT4t_WD4<=%k5Im_?*E^XDy5-'
    ')w_HaG>hiy`}@nzyr`~dd8{0M%C_z&E{{p`S|GB*#cdiEk-@*aID^b;$Z&#&zsADPz|Uz)BeIh{Okn0@o4do|+-'
    'z6L8W+f3ikIs<xOw2X?s!9JRBX}!Le?;Kcb_jH3v`Tb3AdQ)Qq<+q=SbHg7-'
    'ee(w0%BE}kh^_1Mx6DNAy_1)Lez~tX<}`YNwaryLb2@xEbpjouVK?fLsV)w!?TZ<V=C{4<WiMOsFf&O;|E0wbnR4&-'
    ';)3mVPYZoQ>iouT>i%u&LHrM27Y&w}ApEHG<~mjn|4To@rS@v-FMYlP4_W9g7Ad~w-tm|-'
    'YQJV1hyQCnk{(!m(YX&x>^Jwzh9#HO>yKXJo^LE|*7MH)s<&w7W3k8g#zjlli&tFgr-'
    '@c@Kab9Vx+XIrN@wYX(Q`BQebzJ^=wST1Y{U%=uI{h%mdJ(lsuNF1FVyr$9kzATPfUOw#;dV`6F*K5U+3f|J<_Irp66@4L@zOYsi'
    'xO<FD|{qOKx4l%kkbLk37;Cl6ckp8F)|pbm~cVF=0f(IU9>vy~e%HJpsvy%+Tnwm^hhxPcB_-'
    'm&pcRW?|~Z;(f7S=HA({mBr1(Am_g6mTPl{+{?Ujt!1Y#xY25c*7Dvx^P_h4D&O`#HhbfwzxR8;xAiki<}NbD>%@}y32Zm^bb1Dn'
    'UCAd*+#>$-v^rLmxuWn%e3v-r9FKQ4<G00sOn?5lS667a+VAj1UpEZ=w(+;mfBy41v&l!^;OmkB(Sv-WWzIagC~hW3o7t7|sS|Te'
    'ta@AgS*`;4A`S>o5UUG);@8f7?AG&6wypH48#6ZMGuQZ=nd9z5&$}&jzK(2g#uq%KWc~*4iaW6N>0B{%vFiMfeI^!(*PJ`@DSbCb'
    'ty<IV5dPsl*`;u5xeole)U9OJ&3Zo1I%YKYlFvL+XMx;JjMP5KXB0P)XIgUlbY<_K!A;3KJm5^tzLWfxzxkWLX+1sX^yu9<>VcQO'
    'AY;B)V<NuWz0ifOQ>>Owz;F1@YsXCT#z@ka@<?nXct+=5$bU0yqgK-'
    'aedZo^`{wf`HkLT8|9hYJizSabho0R5ck*byA)2sl#mnRlt@^f~mA!OUHv7hN^3~;Xz)_tO-wjj9j6i%wcaHg!3nu4m1y@2dGzxZ'
    '^bpSs)U$4w|VK?*B-'
    'u&h__Z)FCzj?OpJpW}q_a*W5#LAP)op@%j4FB``@Z~&r1ntM1z>bO7o5(1<m>5&ATr$S{$t<<O{3yDB|L^bg8cuCe=1Y(#nROQ04'
    'NPex&N|P`*n=PS9^wl)M%nFcmzNDDH>6|D&T{5z+SlL~>8WOa=YD~i_qC?;JnJYkb2A^pXN%LZT{2rH^Mu%ed_BH9oW|pruhzQH8'
    'BNVw=C}K9`<0yW`MzWS#;%AhvMs;m82m`?qU#K1RKGV5>ZNXu2Yi<e?*GA#Ec-j-cJqAAc?MGKsGKExka<V$6>Wp7XGWd-'
    '&s>~&eqC1fC@XW^=9&g)V8)4NTxg9K%{bCE@uQwgF!Ig%{<DXv7h3C&ZSz|)hb)-'
    'KY$ti%*^GY4oDn=Y<4s<hUN!P=_RT;S=XAD{lN^4UXYtH4-'
    'r@_yu9)NX!ET}huZbTu|Kks5&^`H{^cBo!uJvyI&h=!5MrJF9KB0YH$1h^D%flou>buX(#}$tfrz(DL|JM8{y+*`#`O$hx$Qzcos'
    'V}*nynZ(WT@Ek||ItSu?K3Z)<C@7cG`5lhm2*7vP~w|&9Y*SP_SJ;tf60AG{4adFi|67aXAk4!dGy^Q_I){g8~I3WbC}t;ioHG7G'
    'eBCO)79cG1K;m`i>~6^CsrTaE<8D7b^f;lKiW7~b6?xgF7>6sVS_8$tMnYkS0%4{M$MSreG?kZ`Lqv&zH*b`O!Sd6lY64$$&u8(L'
    '>49YH1&g#oohQTdl8I}j}we##FXUAcZ}~@&wAE_m@9Mb^^~VP<wi8cuVz26OSa%3SA3x8m@!A9W%$&qe~C$wS!MSoXYZ)%l3#w{J'
    '`TqJ%|oesQU}p<Q6A%ZrL8pmfgkvRwn^l8v!zD;K+kW;`DI7YyW*s582y<BZ=KxmyVuVxGf|SC?@^t@D_{9aH8LH$rc2CBat&%cV'
    '0-XTbJWF8-'
    '}SC{sfXy?2>pKKm6!ttV}kvcuWJU~%!f_?Yu1q+dyh*k>6o+HKGj#g@|Clq^VuVhJkprJw|(2U9rbx)(&y*rr=w<LgLZW2uqj*Dj'
    '`@Hc|7IJGUQy0XV|(hj(ZiyHy^oG1SK!QS2lW;DD*wr!{7LI6ae002>U&O}_q^vV*Ci+ZqaXd~Y3)zXrm<f4y4S&<{BKR$rM70Oy'
    'V$kbcICUV0pVThOAegT{(M;0v!DI!&MBf_)%mzS{>$(D&hO0c@3=fWQ$KX}Z)O3;#z8kT4bfixIxOGsFdZ{m)a3Xc^_sQtXzS0+-'
    ';O_y2kbvT=8IqaqCEWN8t|yOG<uw+Kb{(SxQ*F3?i<FKS{wDwQ{B&U?{$5R&)8q{fB6!8CcVdsC;IcJx;pg?8@Q<6#;`cwrysX{b'
    'Ouv*?OvyzaE&GK5!kwP5ji{i3FNK0*=qReJd3|HW>l+vBfKSU58r&xd*0K11d1;_-'
    '}9(rD?3B0nLZXi>e(uC6UlLQuKF*%vdJ+vjo2rj$ma~%@BeGswNINI8oHH^&Rh(3COzvMi2<37VrDCvsq1n!)Bx#&#(sr|iL1jS)'
    'oB&)wGBJs-OIigO)o}|&-'
    'f<ovrn;OwH|6++owe{c`Ir^qr21viP@0dWTHH<x4h*o`)VbY*)*U0<R^PBQ}M>#BWqR8S2M(#2j~WK<KZ3p&G1d}MQrEffU<#MCt'
    '_J6|9<U59dixA77pP?y=w1ZrQNd*hOWjlGkC=hoDVe<_{14e_cF(r(~C{qd#dNUn63kFZN&XE*L4-'
    'Y6+79$lj=M)PpN%(UHpEu<FCi=oBfP2tKnkDyrG>dSjgxp=RDktjGeF1Yg~8MJU7YSvJoutTzhEw{r7+W_r+Y%a0B<)fw_bh_eRX'
    '{?)>^~b#rwNH}Ir4zVVIi`>BUAhs6HjyWr&EIlsqmjz5_EP5mR1x1RgWb=tq|VfrEk|H#=X-'
    '}K%t91#ujnX9w6=mxqi^PAVTTj)OT!?Z_t2d;f*{oSjcflaqMZ!_Jx*JkWqJSUEn+3?~*^i=v3pi%0}gIxscSmji2%*dGMYRGR#$'
    '6a-'
    'AwO>o^;1+q%_np01^+ViQ7l!u10Jq>LbZYRmop_V^Ptl3r@D1P4v<cnV!eT1uCeE4OV<WF|nN?5su_x&L^jTlWr`Gc{GTS?`1~H<'
    '@0d|CW8q?X&xj7rN2ixYX*B+DwkyG>9S8tb@lHsG$Wov!Wbs6le@{7)%^PK1O%%Z8TsbyMbFp5(;tLy}rE1Ct1oAD2?^}fX6*Z9V'
    '+I80({bNs<xWPahm99nOUx~-'
    'nGSJ%JbMP>hVe#!mdZ)I0@j@#%BI?sSxWC34`{De)FPD)>!jvc1Io%nU)>#2)VPZ(ZHoPUiUc@LUr?)_XlFk>6RkI;7RJB4nkBTs'
    '#ZMYoG*!}Q9|>3kr*0sUG2#L2FlJNcpRldjWmL5`K2*4m4XSCpN&_7%(~WH)Wl%r)Sj%+86NvhVIOeCGd&iBIQrKBL=k-'
    'v$58Ikz$cGq}cj22yHbW;|oPG7lygNa}{v^s-'
    'mcg^eP&P(HX>Km57$@EJYLx2=W7dLPMG64P_7&V%oBFYJqX4w3uvd+>%}OKgznh4jam=7BeVWrp6K<ultR9IL-0-'
    '<=wm&^UEe;rG<Ou<1kN%#*U;;ZJ<&wQyz_%E<X@TGnT^eL#MWe38xvbZt|A{Uv8M@i@8;U&3a@@7UdZiOe0cM`dewZXS9Ck8vOP0'
    'uMN&^kwpElLs|nO6z%!2kVdc!JdODxrW%TS?=F8Wx2NCMl*gC%oV-E-'
    '>GNwD9+=2qh)Y4G~mPVGvq|bzmlIP2aA8{Im`dO&Pu=O%xSVGWA*jqe6oe?YibJZRc72JpFVN)8M9d9AnUq@x&KylLF%FBIu87in'
    'VX{z(j|XJeyUsob9?!{=0=ws@3>#qp%`J}gvZ7_cfIbKG1EJGu!t#&tI4lS{~Y(pU(c+L8Nc?J{BUO=^iOWfI)?>Mv%|$m>Kt|)N'
    'ZjYp{jKi>jl}0?T3MbeAHVMf-L28rW9v$c-+S}gL$sg2&&r-'
    '1z!JpH<iK`MKJo)iM^E{smN9%8df_>AFZ+~Ck_)OI%S^9(+rG1G(B{2oJmVRCU+&Z6)1UtI{@+dGln3r}?{W?1d)u4rkLO&EJU4O'
    '8J=b<`Z6B1)*fkFH0KOudg9VLT332+i(eT7RdfnoEcTW14W8QK4=RWtjCvvoY@CSeJq-+yCZhDC$-'
    'xOm)yJ=SXUS360YxP}M=&8pfnic<<x09LoJNNMhG;7+3)ysLe#9HNnXSO-JMUAKD)GUcBicRW+m0Cu>i!q8#W|jrIqVM;A|M#DWI'
    'l=<`-}`-zIQ}&2{La+d$==*=?EYTjOJ%R_<gr70UH=!4J$cDXUb60k)c&V=a(Wx-|7Grm`+N1PU#&k**L<-1<iN}MqC@q-'
    ';<Jm*%gup{%JK9l=S{sJ8<LGuuWvl0{Ev>U{_-'
    '#Xa@Sa7k6<e0GoI=RwVLs9BF<dj**(czlf4rM)~5^px+iYmaeX?+85uL0k2+&dd)m`Z^hF)BbWUIY`q!VDWBlItzW4O4Z++_(+KF'
    '+Ct?C;jM?fze_6D1U%{bRalOgK**i(9rz%tMm=JA@>yr%0R#I(eZ$Y?U0{7(Pv<jCp0#GYiwi1qq@KF>Se@eVZ>Gw<L*@!zg#<ky'
    'Iu`+>K>r__nqgW`4ix%mXYc&|DlH97VCR&1ku0J5erGJDGB*6&IWvz#+a-'
    ';BCHSjf!3&d?culdUGNjO~>eS^5Z~pL>^QQTN~VM9+Wz^Sf>auBJ{2R^Yx;Pdk=;hSqsxcH$rL8)M)34$rgA#a-'
    'p^PIyMg^zEHoxS=<DjtQEQ75Yexeq-'
    'H3N(>wZ2u~>9ZCtQ?(|hw=dKiXURy1<n@VWk!u3K*>J>=w^@MYzplpTAqj&+w_>$+FEJ$+x|cgBt!^V|94-'
    'M>Wrr<#$$r;QVoE!Op0FpsjCnos!7<U##(A5rw1`w7oWf2l3`<uHlR&z>b-'
    'zm8j<kGY?1i>%_ZOAHKdQ~IuL9I=wjU1h%)y&K1I?wlLfl$fDd;1rvhdC&fwkA7+$ALRFBZY-ZMv$MrR|NFoH`>gh>dld3P_%{PH'
    'Y9B+~#CeC^iQ_x}a$`qtNAJUD9WP59*XQ%?#d3GVZSG7wb9b(V5GN8>+!iPE+!W_z!<=lH({htF({HIMaxdboiLtKZobGS*?QLIC'
    '4HVtLpH+)ebX%@<_~m^L%V*5{>7nx}_j%)9(G)GV)B{|hpZ{eh^E`_=Ipkx8(Q-'
    'X?zD@=%*);V%`L4u*=lHti|2`w1Kj<`LMR(Tq9f_B(F%O^Rd9)pS+VYUkoVX7kdG`7F%_U27CeQimrDqnp_*|d0#zXR4?tS#qo6m'
    '25ru`f<<2Tj{H{hqAjNY3*W1(+iU0Hd4o|m1^OCO*5-'
    'j31Nxexu|nj3N7nQp;P@`#30|FDjUp;huu(NRnXP0gQAuXM7sbnL<t!QOVQxh}4BQm*x4eRi{g_srN9c~Sg6+j?|D)4_FYtHTK2_'
    '{@3cc-FZ7zOK^g3lEljySoeLnQ55c=Nc~ZRZK@so-'
    '=KgUhI9$=MDLL1&5mPtu3^3{ukaWduX{v_mQ<lSKyD6*=8OyZ(7GBzQXTiPdG=zHn`YVJGJHeHqLQ<-'
    'rZez+qU~%<8YA|6K$9M3_jw2yFPD?$CX{U(5~#tyXzXfNmu88YEI{SVpnyZU}|&t!O6Q4t0Tw7+|(TZ(l7l|$9Uz@vVY`xjPtV(H'
    'y4}FKCywf;%(dLxC0Yj=(dek+twC3@J&Jkdi?I5>+jdU{q1kxzz5#_?sqRa*<z?<47nU!V6GJ;(}x`GSTCENkHjz1bEIr#vliNpD'
    '4Td+f6?WdVcy%WIeULBZPq$y2Znifn!hz;yXVvYuAI@*Ri~quv3hepOVcHNBT^&BwoMG4jti!ddW`e~a+diFseM9Ec-'
    '81z*EK_IxANifT;~k<ymi0P;Uk_5nR67@mU>gX<naJ*In%7=e4Wobt6IgoE84ZcAwOGAo&25`z34^VM=msDH#?ibFoMtFJ!chWk='
    '}yo>y?_Axz87xv%SQ_@oZw@>2;(>f*LHdPR+I`|N3;u3jPBdSkHplCvRGst-'
    '{Y*(csv%fnk=87OOZ}=dH}IbC&qVd<6L*azWGw;U_vEeMrM+sa<iu!DKxLAM#xCBIf>ea}7-'
    '9Go|OAHR`duUYMT}yd)UJ$OG%T1b&v>Q1QG~e(t?#ZN$@xS2`yTuI4`BO>z_E^p)Mkm+N@e=*zQ?C8d9N_v_HZL(R3?1{kVqh1Z}'
    '1o5(pM_tDfnrH0qyf5Byf*`XUh9^KOWbL8pwz5DE7ICMyAqk<p#tm*SE2WGd_RQexWDX}DR5B)}h4WR-'
    '5uwK)7xN1K1n>LfT{N59D2lm7l@9l`Mbv#6G4smw9H`J<%S)e@(jt__yp2KteRI?W>@eMHnwDrh8#0yzyGBBy7?$CLe>py~v9E%@'
    '$Z|YLuA?Pm;zkGf1p_A|Vp6_|m;zzH0-RrszN4$oPO&=!b{<iQVaVE6-'
    'u^;=flVk9jWAP)g@&|z*<@aOoBeH;g41R={9&7vvc68hL(RF$15PoC@>w+Oob0m(!kJR?kt<K>S1wRtc4Spm(F18!|NdCVbOlD6!'
    '?|ILALg7cHt9n+&A^Zp}j`{9g*cu!}EL^_%8b1>24MubbKk~ldM=yTyi?`xO!9RZDCw}7O`@Zk{u3XOxUhsmGDJTBE@uS+;`^Jyh'
    'UZ<z0Tk#_`4KM)rgf8%mHGafrr2E+`@FRVHU`7@@*V2;`enj`v>1t}k(%C69egwPFPs)DD)i1lW_1a8Bw65=LOu{w6|KLY@<sQP1'
    '^dnYRbU*kJ+{z=`sFSG2E3~7}*fH|;XZ(oGBbGPk$VIQ4EmQPqng&0TR{;Z3&!7f@UqsIZ-'
    '$)<T;74r5;74p4wE;z6`?rA~nKc3{U`wf|F=vGy-i051`?r7l(z`AAQStsk{0Od-*+cN7oH@O%U?T9NI`<p+k@-'
    'A$N_`QVk?oXzf~i?dUZK1v^SWSE>T&qk@FSQA{79Xac{I*l$)@Ccc09v-Q#Z2<KSED7F@CLU-N28$R}6f_pVX-'
    '|W})6yy_6bbOCKcl6EIW!t|!^3C)<f1kyU<&gTdKgV|)XA#b<;c)n{D6kBXKZ*BSGj+y2Q+f#7eh8y-T(vw7<pdzOoHjc0-'
    '%silD*;m7i~;F!T4dUiwE@M2s`-'
    '9YwcAAVHyS>jm5UkiRT$H}HT)3#Z5<aZy1ABhX7QFl%0?F84@g&)=aEO?e!j##IdJ`4$d1Unk_Gvdr@#hmND9=?!1VfdC0z;A&cd'
    '5({u=4i~+?E0P3HI1<ZKN7R_**ox~yNB?j#5A|%v9Ix?ItM3P=CmBWrtjFmkAfF?%p8zy_z^njC0Vkq=g?>FM0#)3|CVdzBaYg+i'
    '}ccwxB8|xy~%mKb^K`V2eS=75?4KhAI;Av7K{%0j$`qoxyRTXw;Q!A>c7P3gQ>Njp58Z^HO>An`Xz?nv0wgdo%0P0V;g>CP4O=}e'
    '0_fVHNhm-_)&0!#}Yp(y?8W!lo)%?0>7|iVB^I8CNC4COuSMIB>yKf$%x|9<umr-'
    'N2@v`^_+Y0qu_AC2<NzB*+^UQBd@(Kew6RHAN**RGw2g6j*pqXF*A0=#wnTEa&#9Sun#{fxxVn;$3FJ4yEE33Gqy!;k|`Vbkva*n'
    'FaJ;e!<dQEHUND8e(|Hy8+Q-k9-'
    '(9QF7f7FvHtm*)|m1k{HXZ(+W3(igB8EE%`<Q}I;3k2f>*QaOQ!VfHMT1|NDhr&?r_8zH{69El}=pnqp};1#*fw*NaW^qagi0>+G'
    'Z(Rf5Bq@{LlaVAb#|=x4ms6maQjyddJTAkw-k2z8lUE**DH>^Q8W<Y)1J+dI`_?(Uuu-cSjGo4g6^2T-'
    '@CzAMO`F+QPGUCrs#Q{HSCs{2};}c`)bcl})cXm%H$z<o2iLWyX)jjKwAP#Rm<3B<@?jLHCl=&tMyVRQ~a@k7Z|G8$Swt_S6>MUE'
    '@cueeG+P9-ZY&ZN-'
    'n&4wSC%Trz$C%QqFDZu>TUg3;lA@guJt@%gqT(swTLYxohogTLrUKj`#P;rEoUD@SyW?c6$kq<4=T*!lC}k1M>bYoOTZup_k!a>e'
    'kJc(GWsvq_%evGiE<`-'
    '~sKhtL3R(cpgYBk~fqz+bTV?K6JFZ@mtFq)(z=()yFLqusB5R(0*&4@9o3d}+NacHu|z2>DH)`qZa7hZCJ(9Ih1)phfT_kNo3f@F'
    'TwmdrS-'
    '?{p<GON5PKf&$G7SN9AXAENNgl{k+f0H99ZyHuXD@Q!5?;Kl;w^{LYgDap1l9(U1T5k2mH9zp|gf24O<>n(qfQB4dId(UYE+TX-'
    'G(C^G^w<7)0vx9)wFo^<n!mec^_U;Y+;(}zV&gp8%%2X4~wJ9-{&Qv2S0am3x!D?R-1!>4-'
    'ml)ZiOs#m@0<mE4a`H8wraZfQL>!mM!>4{pMc{!(+{CexBe(I-'
    'A#O>5Si8tv*GU9&y`S#L&iJkDLzxK7SbuPO8W**gds%3O9uuQKJUyCkC4R88xgnp^vn(3Duj`YS$uaWeFO-'
    '>n|?KAWxH($oJ$V)IA_|ZonZJZW8MxWhX{PZB#2H%$7-'
    '?2G)>2zVqtfni!(3#X1vHa?$DSD=E5?#?C{XkQzKldiaTbbXM8b!3^v!hedvCp7*ofta2=y9gaZPB)6G<hI?DYi-updmgL|3*`1j'
    'Xa9|k{*7k>&-k;XRqYsnLYs}r}XhUmPQ-&e9BXv((8#ruN9tm%)RtXaj|!?bUFf0>cNv5{83lyIW%t^U|=6d)96Xcdox{U+8(4S-'
    'E~$!=vDGoP0gJHw0a=C^aSSD>&k;$xsUZ{+>ky`DET_^>Op$te&=;8t!^sIpZ2t;-63zwF5J-'
    'F&wAFg?hJkPAnA0}y+4Nb!cII?T@!!e=YRg^PfC}!-BWt+&Ub(JcXy4X*(+*v$4m-'
    '%dB@J>BUo@neg39ghwiJ#ZbJLXCV$ZUeI@rn-'
    ';ifN``K{KD?S)r_J6pt97_1K+%&xa;b)e<l6(Vx2>s9A{;&V~FSY?Y7i}&^zqHN~fXUbAv^@<gmFHT1PsbU}*+P3hG~1UhRJ$oZj'
    '-SU~R>#IhSL^6n<S?jtMf1|7!PGZ&g8T<~EW2IKPwivp$;|yM_xPZ4eY!pthRlxt&ENdZQ@tShT5o^*+fU!}mbaYhjaYub#&?_3W'
    '=5Bun{op9o@!G0Kkzd?IXj&XlYaPU_pkr@ubtN-UQ{+^#}Cam_ucMU-K(4ek3~l|!rhVI-L<CAdCqg>4=l5W;w$<5%;p+-'
    'hwZ2H?<{`iM?d<}JKymg-?7|-'
    'S#Q3RPwD&k@91xiw1pP@8ND_2IpQC^@P#jIev!i<e!?d98om!qo*(31VCWv@UdRQgd&HCXroCVrb^b+ah%z@jJ^AC)jDF-'
    '|@!k8;Y`Xeh^z1k>KdbhseP}%g_2M@Z>3#2e--6+qFNLSw)7`sw`QRO|v^SZzIOg5&>LZsPg-'
    'c9cyjY#0oC&!P@+;&aB<IE>SpySSS1E@;OccG*NnIt{WPX5aXD|Alzb!vEF$8&Sbv`!e2Zv0(BFr*%f|;YCZz5b)d=`#U|L=aW?|'
    'kPw+lN<QlvpO8-~6kQuOQcT&SUNx3-'
    '9487Jrfn9g7wBMXz98`!EP{pybiLk>hlp9$1OV>8}C<mwS@gacB$EH&1QkmNb9!)iSFCF2XMn+Yt+}kMNsSf3(Jo%6DI4N6&x$^R'
    'M6|!L$-'
    '5p85keE%d*Uqpa={y(Y}J{UCf~5AvKI%6zKPbG~u)+Se<w*Tnu)XS1penR`s$8#4s&?uq4g{et*lW~GjJx7@YHT*sW*Wo{YXnQ^w'
    '@3f2lwJ(+a6+VQ*V`2767Ep<kH=J2%q{t;(vUR|HJ^sExU5W^EcEC2E!o;0tS_eyWy8~KKJx8wvIz0%7Mj|Gzq4(bd9>m6sVU+3>'
    '#xLfhe1`YRN8xz0wS;h1CUrs@AM0ByIVj78in*TPx{}A1#{pxd5`tb?|JmZ)%wqk9eYs)G%;N(+e6#10Ch*{{H`8DYs=y`bXB%Af'
    'GUik2HpZnb1V{5i%?8kNb%wYEU?p)Uzo6YCWygg&TTQJGfkt;^$@1@<gd=oZ<*pob`F(2Z}Oy$f-'
    'cFl92$#s50aulW+jOIw**@t(n<<T}iiTujz*4WWDJbnkSZD4U_S1$N(>7OfjcIMfwX{OhI*<n2o8qQR9Q)2@9ttB@ui=9LciO-'
    'WU;)TwPvy)mbHC)c`DyM74YR<+?#Ma9tXLjO-ky$szFlWqsrQ4z-'
    ';9ASI)V*Kq!7!J55$jaj#rBW~XkN9xi*gH7&mrc_#)NTX(SvLhzl(Fh1oR?+Wxxy6M+8Gi&Mmtio-*dmZOkUE?_6-iGRwPH-'
    '!8oJy7bzX1CsCk_kaKQIquE=*hw$FuGyq`i9Tnaus7W+UV?jsR$k+N`2<;TBego|x12dm!H>`sro?_9HBs#su_@&W^JC?;KJ%H+?'
    '0KyE`0H0+Hd5y*i`&-'
    'csO7ph<BP9&#VguwlSi5Su<Oz=zmrRU`ImorI`zDlzdFx_!|TmEY%(}U=8>}P<X4~<Ug0y1o_B4BI+tj}Zc1<J^z=(!<SpVy-'
    'D~sz@S~mh(dB*ONB5qj_|fGp<431k@S`Vl{QilAA3f3I@z<v7V}KvscHH@i5|clgrq{ra9w;w8LHYI01K{=lZTQjp`kpZOk=jSt$'
    '8(?i-2cOmj=+!De=Gdx&My2&-HJXVmikLJ^PE#~L;UF8|Mw)rkJttLhO!IP)}7qFdw0Q)^osq_AN|qBkJ!<-'
    'gdd$eM)=V}FSW}L8b3lS^#EV^!WS0&2;TB!!H=AS;79R!ZWBMs{NnXI+u%petywwc1MkC+&Yr0Fk-Fi>5<e10RPS;f{77u=NsJ#|'
    '-X?yOICc6|9g811?|Ah#@uLy*zYYB8eBejt4+1}0-'
    '@`uqNZfYJhj}3Q(bJ#)^!ve&&Tkt(`p^IT&;PCX(fR%0M`cqyA@HO5@5dQGI^TvL&9$!X^Z)Rp>)}VEmTS$|k1Kw(l5N}YqdQL&{'
    '74@M{Sy2QClQ-'
    'H20wbi3tsTR@S{2hCsR(KeiwW3BeCNLg&*mQ!5`5li0!=#KQcocek68VpRKpb27XjFY0pN~SK@y0qx6CQuJ8J;4g6^IRoI0eovra'
    'BJxXp9KeFOC1Q&__;C*T_)wjZq#AMlI>`AsKzSIj&{hB#$UdP@;&;OsjdyTbsyXwN9AQ7X{putNGA(5ROlD*x(HyU5;bjvTk@bW@'
    'lSfhz}H$+3kTcRN#ByE*Tv8P~fo|d*ik*h#Cg#%UELoeqXTEMncnh+)N0u@1nfOu&Q{^w_AexLtXb3f0z?BDMk4*J{4$Xa`?XFbo'
    'H-#O-'
    '(bB^yEW6FDn3&1fEbK+)WZ$=KTeR4yZt?FxMF_d!d;4Iv;o_XQ^xGT>y2glDSgZZs;!AE&<AJ*jFEAt0F@PQsjm9xWwLt?hVAJv>'
    'G6+_?U?91eB8RvU1e2QlWBWJkL?RLLj4`ud>FHmN&k<R3{CU$nYbt2uh4r*(!?knM!u=bYMXXQ-'
    '!z2bax`F`XF5=STR4<ANyVvV(I&mY6LAZAaQ2T#~JBd_6$w0CedMz~&|r32O(Ij@opgeM#;hXgn0m&k=gul&yQ@KZ2>kG6G9YsX7'
    'tQ`7yv&gU1A*GPR1!~#Bu@9UKN?)9OuJ8X`eN-&lag<j}ad^+^jd-aDYdt{7-'
    'D;>shhSP;Vya=rH3;n^X{7TNx(3Z`v<Q$QM`+@J8@9!@1fVi*ajqCYa`2_gG*d^HLQ}E$8^S{0aXL>dAoL#oDqjMtil0FDV$uCLv'
    '<=m7TPt3xD<Vw728=abuua&i*ZO@-'
    'zUefyErM(aGm#V{ob~*U`dZwHE&G|alu1~(ot=ymW|K|ha1K8d_L61)^FTCa)rpe`5bC8~r7t%EkS&yExT%ub#a;U5iu^v4);qUo'
    '9zo(v?)z>oozQ5~t{jTQ)t7F^e`D(kh*!$1=tk3E>H|_he7o`2)bLan&Kk`SGIIe<U-'
    '>cH*tjjrWVn+sVy>st|akt&SN_AVs*g8Y5&bH=Qc&%DKbGPtE<^%lN@-'
    'Bu8;K$`3mv_({!8j(DRhvKKRQfuL9}s@O^|$_3+`e=7`d%xq4Uf#9J4P>h(Th5NWd3HK3GT@J!#Pu5@+Du=`3f9{bJonQ<n+9M|N'
    'hzU|NXze^A@<FT1WFwe1h}hKId~jr*nJa$k_2y&X6=8l~cNnF=t|){?cFiOPxQ#*_i)2ziRM_OMADqS&vCq{#U>H)t#GYYvj%$S@'
    'W20n;(rcxcaNSVQnrBhn_cM_^*4;7-'
    'yD+bMbsUM5}w&AU(I^ANT`*z&um#h<?BDNANVC_|YHz(LNWpo|pSwo=zN~eL*jM=}YD4faOlkQO`5KckZ5io9c`|Q-'
    '5uN8^Y(|=<IQ6Yt@dGy<D)@PPh=<3BAEJDZ5xSxk%tS&bHrquCvmt59Ld@hPEEU2aJ7NOCIyA5l2pM>t$`+d60(x^*AfyGF%Kln>'
    '>lFJUvHSd@A@QIVs!k<dxxL>3;R>AIo07k)yu*jQHT^wP2eA@94ppm-IZq@@~o@YCX@!XfwQ#e4;+XC0R$|Ic+4BJJt949n8!fn~'
    'CY?zcu^R^-0^b@6RT_+4Wrqto8U|=z=nPpYxoPXBwZP-'
    '?p+}+}zysys#suNqjSXAEx|J>iLOJe8O6B@vT_H%K16=iuU}l?fKpJgQL)1^0ei3@(JC_=h^!El6%iQ*;&o}CE4#uC)+x(=akX6*'
    'azG)yU?C{$)8{@Z4GFR>nsY_+ULyQL|4qK^#h#4XuBQ!n*J{Bs-'
    '07p;OM>c8QZ$Qb1tsKzd7GRdG&9859gK*A9L3m7>pcw{WsQ<^0LrxJ`_GWXUz`|X(<C=3r>KKo$!rLzQSOtU&h~iUC#?w_L>V-'
    'J(3rHeiq%&nd0Mj3%{fdN3QbvT>W(?Z|CestsGd5LmKDcEN7U=rNmdJt*p<z@>8mR<r;Fn`p9|QF=t;#n;yj>4Zr-'
    'N=dG>_2RF`}yP9*z&c4-'
    'I5+jL+Q)Zaa6aSCgvmIk~@c*zQ9mCeA7yh#F30KGXM02hFX>HDS!a}YU92@>4Wz_#+mwd8(l=6HQp6==x|8>Exo-'
    'xFZEzg31zB2CD-^;^GU{UVTf0MlrvGZ&&Tjevc9<U{@i%o%JIb&$%Ja*b{>zpiQD;!PutgdJL8eZj{;$wxC_x3gL8_m4<e6HM-zc'
    'aeLirw((FY$mW>);e-yR(ze^UZI5bH`{Nn>-'
    'IjvG>^%k^LnEjyXG!9clB!CEuUiq_e(n;CQvgbt$j5F8zJg=fCINyt&T3&ph_nW3f5>QrFd1MbDyZE6-'
    'LY`TCZ7*aKlKX>&^BSkI-!N6045ecdyZOPd%Yh-XC?Km6ej*L;P1h_`Hqdu-'
    '`r<uqsexn|qeFx$YJ|8$vewfV_TnfxZ>+6JFwPfYdO;z*1$-'
    'R{`uVXoKa6BpK0xD4}qx#Z;KHx?Vy?V~ad?eVX796$Qek6u)+<5jPE)zv=!?Lj2it?@|B9$b`jvCTuS_KXe7=S_Edt~i*;QSY~HK'
    'G^G#@fEMhUyU2#t2S3R?=o-'
    'aD{N!p<;X$a*Qat@TEmq#kXzC`vFCEP?+6D2=W+&EpW~+du>9gL{^Fja(7cHLvSkl~9lgbyjJcn28Ap3o@^M_s-CFU9t;bmy%kc~'
    '5bn5xy7r%JX8{<2lvpGMmh0nj;tDj3{9@XZD*KMtH-'
    'R^VUuIVDDX~g+>K9dt$oRwEOQjL2#>&JY5@FSh;lPfQ|8rgnrfkOzN5WdD|;TFVF7#rloG(W-'
    'HxHtRDKC`vipJR^BzGRFcewR2G;+dXf&YEYBGq3voF*za!$JT$FF)Qcbg*OVXAzy<%BTX;5zy@Y(0x#FX3Qi+;{c?tqveO@Rw$~5'
    'WuAIs@FzLLzYg`N4%1dcSzHWP|_`&Hr9pF!}My`CB@9<%`80(IRe!_Qd-UEMJg#TTSml+(*vhOf)S1CV!4X5F^1=s8&=zEjY%^m`'
    'CDcDwAgAbj88BFbk@xN!OD~`z;)|?g|_D1oWXuIUGbiWb9)XS~T_(5mD+vjONv$eE!v$eLoE_^FTo@H}aZfUVGp7rUU{^=LlQ*8g'
    'IGh5{Kgj={C_6EM{tSw=yuF0#Z|Krj}&ducY?q@fLKg#)B=Be;XpQ1nGn$AhVM}AX2B0du9=ix(nm~n1*<=gHQ4@aCig7>%g)Obl'
    '3>2vrZYuo57`#@h|nsfMKd+2AgH#cM7XUB<eb2`)Jf$IMd`Lny;^Q4@Lzw>wg&VELpeW&&gS#PqlY`*>~-'
    'Vm4jidVdXKkcmSH$NJm=bMXoj{WmTVQb&K^Q-pl$$ySGj-&a5hpnd%frmRvryf?HddPbQj`{8L(og0y4Ifh5-'
    'Z?%eb8KfYg+H2jhv#E&$H{FuVRsju*qh(ld1=m@#Vy&}W8V<Jyg9r%ZyUeFVvAemKkxgKo!N%Jw4a9HlG<P2H`o5}T$Zy4oiA=5n'
    'R9@w<J)?n$JQivL)?=5+~!R<Q87~C^iMoD@lJCF^|r^ajVXPu($+NMZf3m2IQ4iE@jJ#Sxxo4R?MJjegp)a|Ik>rywT1N~?96|}t'
    'hKqC`E|$78G>SZa0z%B@hhMExu1J)to8d`PArz^w(|7(mo-ZEl$mqO%V1v2uPr9ZnO=A;Wy8&h32)Eb84sM7=9zr<Vq;o4&f2qkJ'
    'QwcHJj9-{&-'
    '~2K?6Hi4U+rz9o$!vzjz<#5lvpO%se^mJ<Rvee+r@qR{zAH7@1;3*&c(A1$Xd^<Iu2i0$FAvJpBH@57k$xkhKSf5yoR}${f(_Ybg'
    'bj|@sEGJ@2kZzwDrBcZ?3lov-<|Eb+WfC&$LG~zM{l#;Q!wArZ-i)(C2`-'
    'qU^7uH`>v<m_8G@`W_z&E7yDPoXLD9R!Iz;Gx=~$?&C9@;dFN7{c&ENwNzh^h%>UEKWCRId)7MEIR3{kv^7jWAJ$pZ&LwPfC-eV%'
    'Bc|f!<u8AEZv*SV_PU%;VeTsah@VZYml!GjV{26V^sS}5kBEJm&he=N`+7EJk1KM%o%WIAfvyh>E}I^8PS6>6F#Y3y{EzpTB%CN-'
    'sm;6l|JFG6wu;-ra}njW-fVO2xu4^uy1zYVf7!PW$HZ*;U(87M=)$4(Y31yDtes)t8T><Su75A*mACe|&Ut9TPHulXPT#E&*a_$A'
    'i3iA8TKtE6yMCM4sp=~$dF<Gh#TPo_pSqrk)fh1#-8NX;<(w3H9bU-'
    '#RvY_He2=w=b#L~p>TBb?yrq9N8(rrLm*f1qUQT7p`C2(sY$f*}EPL!0-qL!S@Y6f*pxLe+pESQ{&V0!EB-ZroMeFz0ocFfkx8~T'
    'B_-=z=Yrlm9Yh}83Ox#i8EBL5krQhjW^d<2gi8T`6k!KFxq1*Uow-'
    ')ZGt<SI5;<mOpu;9q=Ykxx1?Y=IzhP0k+I=FM5B3~W<NAiPcV_fH3-trdq?x<L&D&zUJ9=PwF^SE*@S*?5YdBhcU-wyvBeH^^T67'
    'LhKF*M$n7$E%oa#mCu*Y3?RDaXdS=&Ss3*5mZg_``>hbMNCz<XdXvdDq1n`*utWSLwG)KbpATrQG!_xWoXCIMRMDsj;2kp6)Am&Y'
    ')37ZLCfCNpt>Uasvj>aUR>f!r%8cY~$&z_>_G(PG@#@ac}bx<)CxyO_T1ERHi9bW=GGr&d;09(Cd2F)~)wPUbCgl^fEE9vDJwqqi'
    '1X!pH>^|ZtR!-%YXSV_grem3*(M)rOg*^oLl6KKlX-gR0lrS_*CJ@CN>?qH})LtoVV55;oh-0?uj?sD_ik2d-'
    '5lCd)IWha%Veb^qZ=8u%kchn!1}Cu^)V}{C)P*^Tp)6A7X5?rvk?232%Jk8@sJBKS}N<K3DdVp3u#Vk2C+)?EEc#tUB>9WG!xRny'
    '+*&srCE#NiOF&uAIG^vps9>V6Qnlmj0WE8B>j|bW-1?XYsA_!N=Fi-sC;r!2j%#&%FAdU)q@1#-Z5dJ~tj`Gj|-'
    '@9Ai0$HTifSG~R6u!<@mGF{;(M&#{ABn|JTvX3mq`r4juLR`f%kqi<}9emKs!?mqo-'
    'K4;%gXs@6Bn*4<JY_<7l=hBk<fnOTd=JkoK373vz$i4)76o}6fr({1~&MwDW;4cze!k;_x#dW_nKF}T^d<H*nVlI@!+%ID9OJbYc'
    'ql&egXYd_+9!`aLKH(S69=Fsb`4Ws{Bzp#uvoGtX<h#;$NxPSIec!v5cs18%-'
    '$%yi5zE@K8T+vko76eI#F*F<rLKuHNerD=ye8Wqc5D{cM#4qG$T$astY>q7^X3tM7C(CbKk<6Gr|a^3VlAFB<=MEo#F{0}%$zPc|'
    'KLZWE8(N8<r|)to&lF|qxNk?hq8AM_kja|k$QQia^OG-Y*I#b!B0j{)SIq_H^a}s8}2wKv1-'
    '<9tzX}?G2~|K(cO%FBlaALmlFp?pYSs77hMz6lDIt2r{m!*!fPfjknl0slVtB_&fpHt+AAEN`j6P8C0C+3H2#@>jhu<SJo=dS(7v'
    '7lCv8hNa8vH3kHD3TK5{8PAP&1>*z>`><~6VB`6lgywI7;q!`jh$+rCzNk@+<2Mdh;+$2R;-'
    'JswVs6+f8wzy8<%`m^lA{*2G~jDEep-'
    '}`%iuf4Q=|EGKNbJ%a|EIRvk?JI70^&FUDsZ#D>uk1ckUu~|AbThcBd+_y|wd05%?Obef&G7m7P8+d5aKu4*PSc&sW~VOgZD{kGz'
    'AsqLO&EOUXMX0{v@iO(<j)=`cNF29<B#O8g}MFhVhs5ao4#E(n{lbHz!vuwJHm$Kyh3^fqvTZby=&!n(M}ETzGqx6PHp{=_}O1=I'
    'R*EQvlv6ZDSOIC9xAZ{m&PwxIbZTsuX>ez=RKz4LHyYd!jbHY&3T?;vrg5Ilj8#q#U~wuQDWlqzkGG#F=`ClUF*FsR`DUn7aoie3'
    '?E>>1^&Foq2>OGuiWAk>gTz>#uUO%PPdxlZ05H1oGrQ<i|Agb#JoJ0akjx{{+;qw9M<&UH~psHw5kvJZLX{LUmJs_+@eS6<6U*|0'
    'l3J$eH~Xq4}#sSbM?9Ob;@11T<7!TJf<u3uW~8VK9Pmj{DLp|f||4Hp>ol)zDF<C>bVum>U#MD<YdPs;r`?T|AT+<51z|4nEpH4u'
    'MK|oe!;7sMOI<~x5{BH+5L)N@+Dug)~<b@b(?=Z6n!{`XRmFnU+4$o;p+H-'
    'TNOKvbNwrS<*)SEIe1Oi9V+K?KfJ6MC%ofd{i}afuE$$rmRP;fC;J{V^ItJgU;gD^zU+^;j~Msc=9N9);p2}#zWm;t&6#n^-'
    'R9os@=xHn?Bf=HX5TFi*q%ADnA3UHJ<o(3lyt?sb)~MG*y>w;&u3uo3trQG)F*a`&R7SCL43(eUUJsTbY61v@0@q0p8O4BpW3{=$'
    '3eDruDp3YhRht5U$M>MFRi7<db!7#{n0=AM=$J~#a-dX#fi1`O7}O3@v;u!Ys?<-'
    'c5RP8v$qy+B#+|DU;c72nqoYA?h?6B#8M^yLwpD3v-'
    'Tt_7ru1l9JFqb+W_}gZA`}pr;qoSBg7vci#q$>yik0m^+V3#5?lDU|MuVR>k7Fm#k+m(=YH-'
    'P9=Y9b9s_z#1$kJkVY2Vg8c2Dqy~p1CTkF_1m-oCLPi8-'
    '{_&2e=q~USXFuba{q1yVg#|z@>v{74^UYh$4A3*1iTbXy_FA~3%_hVoFmRRf69JCkKovl0<uYK)nFPwSs*kg}feDzm<b(f|q7xt<'
    '(I|IM23wUC$=GpjR@rL$cYg_oX_3QbxM~ANTa^bG=(}~XsM?K;tmY9d&2@i3Dc;BqEiTS*B5Ff4IB(}g>HF<dWxvZ0{H|bVePvKn'
    'qxd!!_i5)qB+Y(FF)?qv2Rl~Edp{=Fq(ck$yf2ZqK6?@~YUD+S{$|hLL`)lj9&Y`=`*%112vz0sN-'
    'M6*MYME*b7+=_k;p=rO@q^vZO^4{NHF$EU@E`Fx#vh13h>s$^57+Z!v~_sDzQ%H-&Ag7dl0~#*UQ2w9efLWorahyr-'
    '^tI}*Tn299-YsFo+U2Xx>;U)dk)(CpyN#c<bxV}!MnW>pTM6w<-'
    'P3uOB;7?#Xinuo~2yd*WYq$>5uFIJ%by)B=LiK^*<Y7z3zH@ylXtl+OraanfJl2>fV=r>6hMLiG%EZ)^hKDj*0mB#A)!uB!?9p(5'
    '|f?_PkQg^5Cn%d6efx*v|#Srn_@o%1&Fa=|G7|>;Llw8ZY=*J=dND!gr*fd(WT5pT;L%<4BXEwBl89t1`uO<=n8f*u7(<`_>cdka'
    'JLQ`>^Df=S$6geB#<scecOsZkIJr?v_5xI96L(@k~r(xB+`+*nrtitm)c}U*6Z)B)<2QyNwe&v0R=nevKrC(DS{<E{vG3g-'
    '0;AAmI?$q4cGhQ}DliVu?d+dR${LdpwM1!1)k{!I2zc>z8&}!)G6cqn-4#i?Qap7-RN=opCTR-'
    'w~hfkvsE8l@r*<AK^&Y`WFy?boFbIKVrKc@kgigM<Z|EGDbb(k51>0zTzvs;t_xJYlA;Jf5aa>;*TD7yv-y2Xg`01uXw~C-'
    'JL(;pMJz2JskdMC7<6T{%GQlg3%g(RL;}<e~mv{mAmjqZOnhfADzG-DZ_KcABjzSq4Gy?z!Ck)Klvwn>|<NI$xphMKQixc^YP9Vh'
    '&hxC(wvIF+<jjC>Q_Hh{wQlB^M1McUP%0rwIM&eJ-'
    'X)Sd?+wF#2@h?;g4{3_#@cL)q_8BHpX+oAC>$}cjAv)Tb;xo!ITZuFK|g;_=R6M_f>7!{c5<Q_&5J==a1-'
    '?_oV4qKc|qchCi|v4}YXzxK1B-UHfi_KWgim=Yv1GdLi*g^vmZXe`k+TrC-)|>@GcQn05ZB^-'
    'uY${HDi?KjM!*)Vb>LM})0P4khg>CmWv}{z$B-SiSV6E&izK<^Qw%k+JIkcK)d7{XzandDv;(Q8=SV{L%l<AGJPsG1f-'
    '%NIxilbkpWkH!pkH%X%DPo4;PQx$0HxE7xr<ckN8ihTFCHd2!*bkKJpy?TDEBkAC!{U0l=3w<FEw-'
    '*b+W`^dM|+UxqsC!f5QldH``x-'
    '|T+oT2)}6Hi>X{@K58_T##>!*y%J>(*Y^tv#>X*nBOPto7+D=YNTTG*6fJ(Hxdf`b95#(RrJ@np5{zc^<qvhuIwW(?0Ff&VR@6_#'
    'NlwcINGEjv*g;k3ALVDP~J-?1w-'
    '6VfF51mPa#X5ZkQ|$|82vxt+=rX*Q<E*g9KEot$kdf3<ovTiEXf5BGP@qPVvzzVobEJlpTxC*^S8@A|Iq>iBu?!12mwZ+qL@I-'
    'bGQ*~#yG=R14Z<t<fLbsKqRyM1grAV)#R#o6C5grC>EC%y~Da-X#|NIysSFaE{9c+=*Y@*-'
    'ZPeG>x+2hS(kR&1oQwDIq{%@M9!KkfC)XW|3ZLw($fs3Q@Nsjdy@UO#p78~Oq(x&}veOgs84*!vvT@Q?W3v$ZK*AYwk{WAy6toG<'
    'FVSI=`#&yWXFY@{*M92@7-<{16#0q0=Idtn`J9Ysg!Ac3c~y>q6mxy;+Fad5bD$cyFudw=im^*-'
    '9}c_lBpd=D_zPnDTIL}%4c`zpU!aCp(tHWpvCaqy~*k6ll_&;M26EmqUqLR-O;p1?~!2+#4}vq<{2ym{=V-'
    'y8SE&dMVvSD$&Jv)NJxar<%ytAqGj@0|~*yzrJo+P%yV@fqfG&RB0_?YTb~4t>1uJj}MH-C6Hi<I+oWJ2?Ykr_S_-'
    'G~D|0S~=)U{|rWASv@~F8nm~#bp1KM(ND}L%-'
    'LG``~0=7b$UHp``k2Ja?|EhVzB$U0P>>B=hEixH*%HuUU~Er_{cv_tlOOZr_IH3o2Qzy%14S@^Ez_&vw6-`?72kT+jHp17k$we-'
    'N=t4cZ_;lJJ=`1m*C8V&;IPs?!F{v%gdcJ;kM<k=WnncGnd9`_SjW8(G&erd$(sh=b)DZ7Up0$XdI|@soW;c)Mm5gN0C=2d3wybt'
    'poW3<lr$+C*JdwWRC;8Bp0MT4mkVY_xpZd-y<h)A-s}*#yZlvvDFuDeUF57k>BHI<YVHSpdWCBv-(+6E0cY#<D7)f4H{eYVR?h--'
    'HOh2DQ6jP34c*9ul1+C2_NhCw%+UI<O||+U<-'
    '_A^6tvvqzuaMJ!$RO>q7W|{0|d#rYG?GLx1QG^);cqJ6^L^be%Ik2DW_<oii|;yOG>Y^7?2Sn8E|M%U1*wek0}bOy@(uN{-'
    'OvPJ*G|H(bx)@44-n-7kk{F?O^$%w6!Cb+hL<rc14C-7akCbk3mZ^8j-'
    'Iem;5tQ)QDI3TE*^5IU(IUL*2Ash@K_<Yw|Z`d>dE19tQn9@dqvg$Zo&wC?K~-'
    '{aq%GYCHz>(}~+ds*u{%fq#;AM|r<U@32wwp3=hp&OQaajKZE;M=kI-M{;Hcgfu8H~z-oc)zxf-'
    '+l5YfAW323{Jy5icgF#!A;rJh5jlRzoC8wOKn5gAi`$Jxg=+Wy0QuKA9?+PFZhCfPCFaOhVk>UbFTM)&L-'
    'hcWJBb~g89g`*88zN=st&`J)!KMHi%EjweorK*Ev@R#&U$|-'
    '@oqH{km2Bs!X4CeS(>>9EM`4oN+~b*6`|B!p|%H<gYb{G9PID`dmBe7X+@!*(M)b&K{zNv1$4l4B*558*4_+s6M8UHpZ|iJ)cz0z'
    '5o2r|NL&__&?z6e>k;uL~k3<aesZBj<FH?1Z?3)KedHt`kgl8S0wiT^OraMJRf=4j_SkFJ!6voJ1{Um?^v2Q`5ew|p42h?lu!8-'
    'x_CeR+3(@audPq(Be7Mu6n$*u^<MJ0>5FhM*6PQk)j{5{K0X_djnT$Dc$&A^cOnm+F`e$XhdvG){h8g>4@TeYwwaHZ?Kaj}r|8el'
    'jqyBwS8WGJ?UgZ-'
    'j~YMVtgHiAF7_SQpx*MwHe1s9BYE%GU~|wmj&(eZU9h9;pY%ze<hAoF=Ah0FRc`&)SwifR_D|noqtwxu>vh;L`XQg0xlPY$<(w{c'
    'YyGh2qH#`5tDkvipEs$iGm!LQ>$i~)u=^{$_ngcHQWobC(MN6QJRb8Pa~$@8ZIBa>{Yc(CHkl9Jd0ep2&x+4!!Ot_)gI;7VGWwhE'
    'x_uk_^1CkT)3_+Q2e)v0&RlKn-'
    'N%S==2N#Z?y27zYhmTR`nk??<$yD9au!+Bxt_O)kBSen)#nC=O$V=>HAy$kAz|uO{~rCfpW|cxDZj9}H}PH`8~!@;jfO|JxlQB@y'
    '0K4Q+nBr2X}G~q|0bEc8e{oO@fh?8mV^IV=4)xQi2uiDUH|ZC{%W7*r#3gxPqTka-'
    '%vI>qHgSsy_w3%SHTa9`%y0Vz(im59Sr0Fv^KNmlvk|v*}gWh$5CH4M|N%I-'
    's67#ch;Nc`_`<)|H*fs9944M_|96%dVpQ94p0s@7N+hGbNIWzws4k!eu3{|kBwVwM{uJHnQstdXZjt%GdV8}W}}aGouxZ$KmCV^{'
    '?P23HHh+CoAtbE%0234J=QUXsr87m^Z&qsuC?-7|1Ej=t#@%sKKI&mv14oPX8kjM)BO?Fi+mGRtnaN+t?~JYe(I-'
    'w>fV3(FaPD9{5kxb{Mp)+J$6<a-G-'
    'U`qr}<~#yC6A!(*`{?f(U<NcvUq%$$wx;?qYQO+OD#K1S=M=uq^5ZwW4P`|&MU^YRf`SJN#%W}Hv!f4!XWc*7gs(ATs4XQa*Tm+P'
    '%}<>MOb$1c{w{#Tc#E7qVLD?SjfS$9X;TD$w&{>{JnHw%8h^h>{VPYy4>Y<u<CPG_pMc|q^*bX<L`$0Gixm-'
    'Mkow{7}gVr$@)zB}tC{EVk#J>v7ej%jVN_-d>LwGj-BqpdB~y|=x*ZhQ#x>T5s!gw5j9pi9Aqz-'
    ';K3Yy1D!OV;t}cLWCrJN_hi!>amt;=A+8AIWFg$`QY1KR*FK<*YYzQ}ai9$d}dnQ*UQ=q#w#U{G?r1oCRd=C&try2##zWJI2l%C%'
    'w;DnVhu7Yip-*)+JuM`^?lWdGP25o9{U=<ojvgcirG?!V%zr*mruUT-udyh(5vvcKRvZgkStE`Y`bw9~yrgjI<HVV8>?`|0m(+i4'
    'QG(obSXMA0Eb(X8(Gd@C~ptY^rjz592j{k1OA`^7e7mc*-A3ugnABWsaNmlew-j)qH{7Y;Dx%JNBgF<gH<~nQ>8{<;&rxVDs2-'
    'xaz0c5ti|r$u+5evMur57$4xN-Ps|&ocPGu3FW4*+Q-'
    '<!??~vMz8gPn>>cr*4dlD!Gvq(vH(}e%|Jb26&UHVS9H{h|Udn?>m*MX|?%{hraD74kUi0OwW39{ePr7Gbo3&)-'
    '2*!4Mz|CFFar9?<zhTISYkq2dK<{DD+NbwDzE*hhd(ko9$*(JKs=62-'
    '^nJL~DSAi$=x_AVXLL{B<!^I+&N`{SYU8%g<3IO*#$^6Md%#;6dfl|SJtM|4?XIkF#UB{I;I5yyG3?&Y{oK!WoB8uU|MUIzKm3RP'
    'fY0c25`C9{2!7`7{7Pe;)z?_&veu;Z&zcE__UV|rnkSkgn(GHg{uD8Xu_5NgFrYJ|4qYG3iJJ}S`e}X<f35$+E3k#$n{W6ob}#-'
    '&_oO#IbDch}zZ2NQrAgOa^EvBZ<HU%|RhQl`l*jejZTOaz=UUq|oxRt_z<dAp-'
    '~QWsAN$zH?)}Wq{LH=o_#gkHap+|JD16cUdI$dK`eE=#d;#X>Y>%~f*6r+il@|(s<bLk!8OE>Yh(EeMg+DTX;}^Gn<)=5c@g>3Pg'
    '~A`Dj)(Xo_kb6S!*hf`^7(`EM_wy`<er|v-pjLz-^U-'
    'x`DP8tx5f{^&hv@9(D@^6277&9{j>{g9s+;V%Mk8}t@oLF%={4ve`LRkbFAoP8ykPs_@m7C_wh&ON0mQ{kJP%{x{{rKK>lc%-'
    '^PFK{>BAsXXASKBXbhI$M|mXM||w|kny)QTX=uXhySqoBmSf@KkMf|9O94EnNK33FBs3wbBysbe`Kx{|Bv<dKK_UwFPuyGqwp>22'
    'iHCPQ9pM=pZ(3h`8Rie@bkeR@fCzas^YV7VfZ80!Ni&+{v5s@Yn93$!6E#SI)+Drp|Ny}KN{<yg+DSz5WYS7sqM`7U+DZ%#xwqEx'
    'WQxa9cS_D(Iv9RAHf3`MAyT0=;tJSPvwtX8%$t3^G7*j!*BFi{bSgUg+Jm4uKbbqRA#o24SYWNBix7ep1GDj+14E0XRUn6e?mX_d'
    'Fjv0AHi+xSMHecf$|ly4Qu=nJI9Bpo$2SyAKA0*v-t1V_#?k#8wlH=O~R{NOFf_b5uY;-'
    '&Kyc#;EPSa2!F&6O&9S;$~yB$cpSKdKjIfQzF6<B@JBb{kKj1-'
    'M`NEue^&T_aFlF=a>VyRKee59^Gx^W_j_3U5jn&k;f{#D49D<C@U(to6WJ*G$j30al^y;_U(~OLpQvNuEET?kQ~9HeU)k?a`J>oo'
    'V~sMvR$Ic6{=yOd+GmYFq8sXW3V($2;Io&z$?MD?8M`Wflz2UHS7KF^8856KYkzf``6D=H-'
    '1XXYv!8Kfeme6<co1_~{s#Mv*Z3pYxhG%S3V(D_`6KIIJ~w;1_4Pyik^Jwc@JIUDn2+!SZt_PkOFUd+Y0OL57dFn^OrJ6aRQ^c))'
    'Xj6ew&(V~+{#VgcK9Q{2YxxYnrB+8&-'
    '{^o?SI^7xFWvc${!K)4K`7`xG$fJxf%|^obkEhkN8)@ADx|@^}cN$MHlte${)drZPRvm7Jb85fIm`J^;b9h97kLC`LurOJJ;}e+5'
    '2W4GW<!_?|m)dx|u)XH`Lep@T;#XGV@37?YgY1o(ujcT!?;`c`Y1asDGM|;y>tX<&R)uz0<}F?QI=*i$4<YA?}EN85^=5;r|&tlJ'
    '#ZxE%1fNIb$8fuS914$l8wIsNHk%L$C2i*5%fc{6#<g(?5+n!h0OeACZT_ADLr^KcZ_hf27^C8BDCRD}SU8);`vM^eBEen1nxq5n'
    'S55zF$vYtZ(6EeLeF>*2C?2-IrnA9$ycv_?>3{sNr?bIeq-0|Lwp1x96QdGS=+lkJQOoWZ|qUf8;!MeiG|z?MU}3e*_bKD*Y-'
    'P68z#LnE4~P^W(?A#@E9K;+3B#{<MZ=_ebK6a7e><d5}M{rna7^BM*~58tb}~`6E6VWyT*_chg(_CANR&k6;)aVdd5L;g9GkUuOJ'
    'od^)G_N9+k)j8knaxy2t<p?431KN1fIYkPAJ@kji{{?||8tc?6-'
    '%8x&SHC*%!eZKNX;SS>?9~>gzb8jF1U4BQtGPW<i*$7P2pO4{>^rJQY2<{JqKQfj((=caZ8q1S=Y>Ph%-'
    '@`Y@ez6<$%{T!^b;)=OXZl62)Xmrct2$n|pRyPJ==uPEbY1x)ex=GEHC-_F^>$|?9u|LOK8io0cVnH|^)G8t^Pyw-BlE2AN9s;5z'
    '2bE6M{K{(%roH2ubsUqv3HU9aU=94KGl8v5#49E%;)qeHt8YpNBuf&JoY&CGHG9JsSRR3Vvl1>@*2I)T%q=#2)m?D_@2Jd$I64l0'
    'A?_Nld+Tz=$n404;jBblU>69*=u+x7u2!-DA&oe)#kPr`i}k}p4hyG9_I`#l6mAfQ;Xf`|HDyRv5PoGn3|K4=(c?l>V-'
    'prOO26<@1MO<=Sano?M@60+}VA;ZTE&J{Is32_>2zGhdkT$_&oboa*md{hrG^mAv`2JyU$skvS!!%{z3Z$Ui6|DU64=z^iRKlvz$'
    ')tuVbh#@Ma_Q1@j5G;WFu@|MfGr+a5g_({<ycxdUCrqs;ML=6&A#oQ_rr#}wSnkzof%&!v}j?!x{JPQCXLxEnXjMLzL~Pt^1J_}H'
    'y=&kkXEz_+)oad9Em^K|~xKJC*kh+LEH|BhF)8@=Afn{h^Aw*kZV(XoUfJ%k(aKOKduYxIAg(IIwY=yvbpbQG2(b286^Yre0XlD2'
    '>k%rbUl{x|kqb&Tz2Qx@N|2{=acyZ`Y&{zvfaxeMFacXmo&p0MR-x@cpJoQVDGV&|>Ot81;^bgtX`-~QWwyR}K*+vDsw-'
    'y4gR502&!aGLk_WX+&H`aK<`pRk3uKG^JA9|yxXj(9G7`=Wmlb6oRUT%G^Tfnei#ne)|sTD7l7Z<WXXH|=1rT69xxVfi0c{3yrhW'
    'cSxM``B$GyQf@iU&COD-'
    ');TgT)XczbAGcqnze=bnf1Ln87wp3g&Dn5=FD${XLOXF5Z9*v@eAnpbTsqc#B*luYs`aX_71Yye(N3tZW)W~eh%e;Gl`v{n{EBGg'
    'Jqj*o*iQ^Cmhc{<x@UId}2R?SpSvZveoyj_^+MA(Q|?*w{stzg=)VU?97+q2MG@ePklLh3CHlWK8yau1_XoPZhX+^>1g&B(82KUU'
    'g;}*^&4|J_YOY6u&$3IzSo{vV_UPZo9W|Xsz)6EDZ(e)=RD>PIQ^z)-'
    'S0YbP(^3W1=(bKY5Uo?)@Ae%=Ng@~mW}^Cegyg!8x^e7!)x~S`9JuMy*^iC|3t^rJ_-FDcEb;0{o4QcIa^Kd+{bU{eV8O`<=`1#4'
    'qc{~|LH&dr;O$1wx{IB<iG70sE@f-'
    't4CjB*yG2~S8;6f&OZO4i(;0o8~LFKEMZ6|<CC)9GH)Gg?T%sQw;9{3J@vUd5&xI5quWndng`LvVI%ni`g?m?>16cWJ*%IgVi^6*'
    'b6jf-'
    'H4hnQ5?jxo9ixMM1Y!spW__(>Z*tS2zMlR3&;NXDHS?bx9RKhi{=?lT2S@o*#b15i=Y3v}2hgv{y#EoF>F3oq>6vwGpZA@n{|9fM'
    'S@+RR>)EmQrSEIz-!ZP!$;{9F&OK^>t`fURTu03Doy#iEZ!5<>9J|lYTBhOHeTVdgZ?LUt;`cM=;QP)-'
    '4y*;o_FeDye5BTugV*W4jQGasB|KpnUqIDQx(U<ZX`ITK1Jk*`$L9GCp7vncuSGYF*RZs2Uti}(iT%rba?3_WqN8KKb)S#Omo&~4'
    'n#Y&LcW+H-'
    '{omeSsxSXst7FI4HT(kd8Of2_=8rpLIvkDX#vyscvR3Ao#xYt0^UVay>R0g^|1&J%SS30Nuk_1cnKdr`^<Beu!IGUc52KUzCRtZ&'
    '6W98E#VL}xde+nWcgD7nQ(Jv@@(1y`CSI4{h2P-CFMcuZr;ih@UfuVnpYv7Yo!j`^_v3uVXMDyEj?D)2I2XC6aRmI4I9_=2-'
    'SBy^m2EzoxSz#WmAyrEUs3vba5TOL$JotkKVb=L^UqfAj-@`XZ_AB9Kh4GHA>R-@D|Tx*)?5L`G;`-RZ@Kua&-$#6U-'
    'dIbV8suJ8^dum`__Gd*~i0oPhatCO)onim3dE_1L0Tf;bMck?*@kWxXN$QO*kgLEqYn^io?<vHTUt@%#7`k*t?9y#w<9|OFV*kki'
    'Ko~=69rr?&Y`Ho0k2+v%rx)vXgATJVWxcRnCJRhChvu=d(ZivwQt<%l1mR&YlhaLNV0*uDCaTEc+0GW9#F+o^o2r0iL}B*^dz%qm'
    '#i=AIC+`dKr5e-3*?Un~21IX5N(e19-OavHNw*Bl$@ASUj`YoBo^lR<dVr4NGFJ-sT`3D;%bNOYh*PA4hy<?*M;Z_Kw$mPWXPD=B'
    'Iw@r*{9JJyAH~_%WJpc3UcEpFJ-'
    '28sMn)X*d#kiNE8g^;+=^j>d6VR)2KjzN(Jau|4z8^m9Tl*#UOV`e*p%T;p8%%T^!rvF?*JHd@1)ABUHjVxa7|>U|PcY#<#ZV@&R'
    '^bP>MvjQ;UIXD@*mOZ%M67x5zYa^O_V!N<C%kJaryodaxb*L4mjkhtHmf1~4y-'
    '=>=b$Ii!Q5AB+M2G{6lxWLNutc>sd)ipSKyv*<$xz7b3aMJ<(ZrRrg!^}-'
    'H&uMj8?0;LY^*vqoQjzTE;9ItLz}O7K=qbJ9BT7syyU8C7PkR^aIkrD$T7UQP-Fa_#Xt<eY>emsr0;in)Rdjyr<><KLxP#x=Z+dI'
    'KS@9%UXTqy~9=!eD@93v})lWbDwCDFc`JePjpQL~GHZV8FwewXE?*5kVP+m_ye0vpPXa8pQ$PBzXw%Hp5bKm=4Kc|=3M{3V;`>gB'
    'Zj3b^<K2y4j*UKImzZ*FUlEbCrijOg#XH3uj-RN!XLB%?IFpO1R$3Cw`j9=P-'
    'eh(c_Ol@C_HLU2yl9RHHpM8HWewIyY*KPV>*)zOI@X4N_<cF|t1GdCx*(2+7xZ10jJ(bQsvzG?fQlIh3pZv+4a~97ZyFu9F%n7m|'
    '*f?iCA3i#~Kg`+Vg8L%o{=wfqq1px!x?ZK)6WGfA+ps<x`>?uAZ)2vphdK2@U$#9$;_`8H#)jm6G5%J8pS^#^WPh+sZWDMDI-'
    'Pievd`6cV}H?E_Bu!3$G+db&zYUD2Q6ZL#jeo#ypn2X>{rTbY<X>`x>q|ne|(nx7sdqfHFUk{r#@EKU-mig@WaNdCf98&y0*qN?>'
    '1*_YxjF?oWIxRBKO|$j(7C;ZJh7oyGYadF5b8GX_qz^xYx$H{y9F;eOsGen^Wi~_<-'
    '=y%`RTs`_krR*X9{*47~T`lTY4j>oCu~_Iv!2@qzvs?~m~(A9IZ}T5uXoNBg*Ad@yzxFA^UXe`DUa?|PZ|9x_i7!`bxq%ANr+<m#'
    'thFqNm#ny_Jdug!h#wY5gal=z>(4qm~p3M^rP5A++{p!F-'
    'iH;w?GnRwA5*V+@Nd@$|Vz5SYf?|WISP5CgackI=*2lv!7SJw74kNIoI(^|p)OM5Nk^iKRh`~0%?iQdj57VUb(nRd+Dn6!hVSO4R'
    '3jrnapaNX7baKGlCZ@SubC3wOKzUm7%y6XE#n_Jy`>ZzytHEqo6Skg^%U)(y~q?g41a3#@ExZ_#;Ufdl{)_x%8JGHs5u?Gg{56W$'
    'hJ>s1^vd;x?gok4T+h@HmDNEw_@RM{@J>VGZtjQ{#bcMiE9bu|&&Yz{%`aWHRpE|ZRea8z{u=9EF4%R-mZ%td$b?b+5-'
    '!9QheZ9@)uFZqn`{kMDaqi16i078yK+axyn#Bwp!x^pdM{RCrj1prPKXad7(>wbljM;5G>1E+p!wbSuKUZ#ewRu*@ugy6+X0cuBM'
    '?YZbfA78e-gW8wbc;P>JA<iy987&iN4*c8zT-Eg-)yscyPrM{I~eK%ReWbJApCKwp22@054^ms=1lf}-'
    'i1GEW2y0Zi3JR&+A!$8fi_RO<g0J>@B0?m>{0$+c6jL5(LsA8^BPRySZ$d9eNW)ZrpcATo;Ca2`!*e<pX?gU;1>+v^PczgSJ-NAx'
    'Ud;s`2~zM`q1zR_V38xtl5KWacbFzK{xS`a+$YzAui}BF0S%NzvZ|57IVtJM%J$8gU*REM;SSEFWOX%UUt7WjsWJcHn+E?qO;jUY'
    '|PQWE0+3p#@6&Xx;*rzV?69yuOlp)jxOVT#V%OJ2I$}HgEg%Ccm{h6H+`9XtU@of8GQAHk#C~!1+@RP)zN(D)Un6@1M}~Wp}nbm&'
    'gN)iy>K2LuFZw49j}wiz#84U$^Lj)n#a%UQ+gUq^?7*4mSrr6p8A}Oy$!vdbf(p7>C@^P8wo?$>L2<jUmyIG5l+#;2uz1u<vKb`c'
    'j@%|-'
    '~ax5KlzhCX@3Y`@c9W`rt5FyPNFl`*Ww7pRq#=X>8LsN+dQ>%==wgLwU(rV_)I=~dvCnwKMAg7ZPfSvRZP?8N$hB~r_n2Q)z{67;'
    '0L?+z3+Y9etHj2V_&<b>oOadc~8Nvi!p{hrH6%2?e;`l;hLR$As$eC#vvUvcOSVQyZ&TveBx5<*|kTooNHu0ufO*_XnaS0*XHP5>'
    '<7~xUiERf61WE2`0_KJ>+@AdBmSqK8K>wb{nFQsMaCTX1<z-'
    'neYWeQ{>_K#H+BC>{P*GYiN5C<*)yfBV2q2C+rE|SY)_nP$8W5E`d&hPa>UT~HH>vVedKQulazjKPl(^ZgkQs25r=2(nAj{_k{AV'
    'eied15FpXcT`lgKW+9jCAj%KWfF}uLtj{ef;-mSiUE~J0Mu#L0&dmsDQZ1>Ps8Qb`z*Ce*ZD|-'
    'z~d(GrzZ++{03qNa1YfSra<pGetiZ6mMiqFs5al})0pO!eo#LYNsq^%2k{xrYgZ?Z4Z+Fg6_qgc1&_Hdj8rts8O(aqZD$C$L(&^q'
    '43kYrApYv2pdv8L){j`1AFj*rw=*#*D#8oc%i4C$u+Z4aRH%o{d4{83$p6YF*B^R|}mdc?<U4W2c-'
    'HMZC;YkT@Q&d=&`#qGMjpOc>`G2r}E%{DB45Izt6JUF_ZUcxfES@A5od6P9!ggu38=JvjC`rKdjb>l;u>vk;lar0U}WPO!Rrf*mM'
    '%lv>0e?Wh)&ubfdE8Dt<uAPrFug-'
    '!QU4s$vng8jM7)pK<z7+l!ewD=i;*N|nIfv|1KlM}jtGkbrzg|DaLlM5x>PLd3J}!1J{T!ZjGgum*!r9FnNnK;ce(LKm^&NcatT_'
    '^!Y2B_rvXO9v3p<dUM%m|7@r#`dhiaZ_oWh&fGenR0>>|~FWbF(~{v9@uJ>)-'
    'yow!DPx;WS5MK|vmV^+tJ?(rA%#lwp}#xDv>I!V&MgJZBH8Pm6LOh2#VP!;&FtFD17EY;sWdTT{%GV=)g(u_CRy9KAJn^oWl?>5K'
    'kK2g47eo*_zvxmI;M-%@EKU~O&MeV=i%S+s~I0$(_hA#HGy7e|&C@vJAkv;FQg{2s#_?e@Z@!>}|;h3@K5T5k1$SwN`N5Zb@-'
    '+T}_B4Z#s)B1@%&~4s`QRuu=_|eGtzv~MBs6H8Aa?V4lc*X~+U-NUi)>xun!;)S)1B{=R&voSWT-'
    'J`i?YI55ZU^xm^iiHlIaY#Ya2)Y-JAV6t=VCMKcpkf1ajg=3GylYez?Pl#nOC-wA4+Z!vDo@utDiD-'
    '9n3m6eOrGYwsU8FEPj_CdE{JOa*pe-'
    '!8Ew$d#`krE}C=mBe(y1EcVL0sm~vANQuWcu8aS*hY3e2E;qQ+TUgdU56k52P26j>oA6BECv+5!Fb>WU_BH#*j8$yuh<E7zFTQj<'
    'T$=;;b{O-'
    'UzSgjgZF+obPDpR?x5>K!qvX2qe{yjof4UeX`_ug&J*Ai8li<iUuH>W;FWhZ`c{=;bx6WUl{Uq_JPkhHR7Qs04r06f4jZf9K`afg'
    'V3jfi^ugt5o2|cIB_&8^dThBVb@HhO1-@uRB<Kz<~-'
    '}HHNZ30KRHU=l2{04p8@W<Cs^56IIW5mz&&!W39ZPH_}*~lsHivGTERBS@!I*k9BTZPxCTt?!}E8aDhd5X#H`W^fu^t_7pNSn}gJ'
    'W|;U+2<_IRJ32MeSehyRjm2QZ_x81BsW3?wqA2)j`0MSL@%SC1JfRZZU0umv6qW~mk#GIZ8Nu3IIP$d<KK{rW>>n%FC$)m*s=aft'
    'Piw{_Q{$d+%_p|v8BC|b312k4x5y<L*D~Eix`H;zVFDt{Fndoc@=vt_KC9#s~oz1>mHtEU*jQ}@i>H+{rIT|?&eVW_et(S?5`t-'
    '>Q=AKIfYf)ntw;;?+=N4re4R?AsE30o?ffW?VkEZ=6cQLUlZm0@gM*3F3yy*r;g;aDr<H0x$AQ#-NTlY<rutSb4br?n{U-'
    '+)Ti%v-4gr7><1-s8;tx0{nb8j-_Nq|UiJI6-xBxTCn--Ym)Cs1b>AVYZ9cbuY42Ol4-S#JJSh{L>|H!0uB$TNf9-'
    'ko{`2pTd8Rm_Et&5(%iOM8ZItpJdiK6D+K(KOmz~HNN$UIjUuFJXmHfsY-'
    'C4x`RPou?wRe$OCuiM(amu~cJ~K`gqgv;b`KNyBr+Pg;_OXv$<H3IBXMUy&elg;I-'
    '??V4zt8ID`9G5Tt=;z+nSZYwRp#qweT<%@&b97oyV~CH2qtS%>+!Qc`?EVDCjLMF=l|SAyoLXV^!N+cq?~KNU6b4|BG&#Ckr$@Qf'
    '$MkhnEOGnsX9}2r?$ta(`G&AdL3K8xjym_{MY~bU%ULmFZ{wS`Nd!S#l0f-'
    'dX`hJw@0MNt$tNy#;*3cHJzCCV(8TlPFr}S?rZg%%G~9bfBBbh$$$Uv|Gmflo+5rzW&Zwu{?GrpPZsQg&1_GiXR|$-'
    '@Vc)3Z%wae-KjbhjJ7bT^{Vd=)b06@1*2dRe1gTk{*?do9o&Lbu&Vks_pz#5`}F4pfYT;^L#K9Z)FFMTvJacN5AM^e7cfS9@w3MZ'
    '2I{PiUZX!%kG5>otV>({FY-'
    'di<bVI~|J`4YZPyWly(;orz@+Nf-0v!8cd);|>RA2Cul&kp{e1_6J@>eH?6Jo#oojE6X76SjPn`RG-LSaMeg4<~`d=L%*!^1Ue{$'
    '6A)06f+JJ#2#)~NQfmYgU%`ZV49{)=Dy;`=u@H|L-'
    '8IiJ(zkNvSfcK#>+#Gg2m+ZRt#@&p_u+ARA2tBu>9a(2A<PQ=_k`Q(!~ay!URE1$UirS_T1YhgW6@}cZV)8G4l?$7<X`+xq=|M~l'
    'W;V=A!`+xS&{#mc*-oNA}FFD75*@sRi$JzAPB~Q(@`6E5`N;mhlv+sTt^o)JKk!#>vzU5mkoh9%M-'
    '|!8WV#r?en%7*)<?DaAiI;)n6Hh#GY5%lbwJ;@O3i<Zrv)}`upQC;5|EWLqr|$omKl5kqf8OVP-hHvbf9r4kt@FS8cmMAB7k}{=p'
    'Nkv$8-L?(oY|+@-'
    'e1T^>zU#<zv`>L>f#H(@Cz@TZ6NohoMyOEd%2I%QMN~YtG(XBWuJ}O(y!Ln^u^0Jyx|SXci}wrR`!cmzVek9__fC$fBf<-'
    'Z+Q#b)$#i7@BZ!^xd`6=_P1X)Ec<8jLVe>meq+B@UI=+RVJ!y)EZe-LWA~^3^q=mp_>jN$*Zvy(&e}82zU<4s?CfPPd)b*hDRTJy'
    '&A<6K;n?wX&ENm~f4__O?V1aDg*`)#j(5H5U6=Cew`Y5%z9J6(R2){ZY5IO;->BRN=Blj?u3P`;&wT4!-'
    '>T1C%98^t@$lMPES6W&FuimxdMnqZxX|zTj_<f^eYWF9Phpq;>0`t8@|(Wtn>yak;MBjx+duvE({${<y;*<#umAP)hS7P$$Y<wGx'
    '9H$m)2~I~7+hO>o_*z4er1=JzVxMC?4$Ob-^oF3ueMwiZH%I?>e0`0uy;gXk#CEg5knfkg;(>@HV^e)j-'
    '(s9f!o&a=z=j%JhC$(^apsrOP}y8eG`VTgp+<tkF+O&1&o@$b&O_dn9)Q1_U4`Md}o)Zo_eZ_Jizi+I``&Be&k2aKk$JMoFZpG{K'
    'G%INc;U+)2kivS(W+w2bB+f=tFy@wZ)Dc`o7BA^P1h;k*R)r@mZ4@pOkT}tj9>}gFABI`imd?u^-'
    '!!k9_1KC&}9H+v`$?8Mhg)hQUet6>+b6Uv;hcZQ(J=t@58Lhwy20xE-'
    '0kKUBV@4cByU1<zo09?a(Jf@AQDc#hXo@jC^>=K}vpj>2<a|5)pfv17qAc4wvhJD+d$mo>eJwE51C9MGSGzds~f<v3DbZ`D8gRBd'
    'S0srs8W`%&@Ps=wDZU%F`Xv0KvCH#@R+O_ljR^Y0JIq5Ie8tjW|K3sy6>`!HG4fz)e$Uh4Q0Kk*ZnO%B!Xa$I-'
    '0b^W+s|6V?zfBmoj^<HV~g&pymDr>*-`4MI9GUHWoJD@XjUGv->srC5DpZv+oHt*e$Hpkof-'
    '!)a{`sY5mm*4M^8~Hm=kb~vPXUfs)wWA}X{C^7<uN4F3`*;8D-|fgsdHVZ&|L_0(zuysOaJKbzf4}nkTlb%zGk@-'
    '0`^59A%;h=s`>CuueSxgCbCFwRo}W3FXTIiRAN$y<{Pa)%^p0$OzIELYIbOT)uaLHu*^zudUl*CbKOndC=}`M0YOlF{YrW>OlArz'
    'ApWP94^!jr@_j6t5?`O$%v$XXee^GzkC$6b-==(`lbtpJ!-x-'
    'fXGV4LD;}PZRd;<CTpa1zT`G3gOB+GTPI2+{{IrN)f_=R8Svhn*JtV(~_)R(zGtm(syPsOCxd0%;tm0$X$U)mAANb<|S{L9D4LB5'
    '86)3v$pBo()g+1!6f)$JLRW7|3P{l#DW#k~>?Qolp|_OCMEc@RH+D!Q^yfAZOyj?CB;*~I792!DCg@VaSu-'
    '88Ja_`mkyp>s#~w>7M)F1^tBIh+tlKTSD(7T@?DIWu=QS2mBy{LVOROu@&|MZQe<!J^_e_si1vR{Prvg|j3Bw_a{%IMlH>`hwF5z'
    '61|B^KU=!13z&7)KgELzxTcGJ%9S?r@POft%2cbY+3A`XEdC=E;<#wlp%fBXYhm95$*S!i#p?3V3jf}r|}zB?A4g3E@P&86S`Bd+'
    '|iAp5BJ~w?swmR&wJi;{|A5Y2k*o2eeZi8EYE)Ehkoc{;8@okeNMPG2h`u~pJ5-BZ<Kv`rsvJ=_gv~^(X*Zt8-'
    'K{2xAI<<GS@je{C4Kz4a=@W&Y6ilgC`xbhoIru@e77@@Y!ddJ%9iE-'
    '{1XLUW+gF;zxh<M?0oot27(X*DJ8~ENwc?Vfr2s?WRr@NAFkq#hvBjAOCpl%vE&E{7l(a)+;w<EpfB8&d9v2%+E3&(7CRA!LR9E_'
    'd|!fIOKnaE5Ca56ld7h)i-'
    'pN3>{U6uA5aKtNsPYWANPA$JhHOJ)>LcCv^?5f!`ukAG0o}msux8C(3;Ge#2_7G<<GJ!}YvjcK+cHf4IMX@Pi-'
    'p+5M)A4=nEQwcYc4P4e7G)BQ!tXJ`NFU;V2y{<-'
    '#gz9k>|$VYa5zb5rrqpnqUaB2PYmZ%GChV1+{nC0_!|3mnkZ{afIqwMNe%fBX5eHYv!{@)`f;kP13=|sWjmc9*rS-wAn&w=_M6qr'
    '^SpDnn3^rIi$k&5Lk(ZQAbZOT-'
    'h&Hl56UBz(i^F#V_q#o_G|33VJUGQu6cdtws?#1d<{DNJ@?9_Un`hDrEXVorM`&9L7mRaAnaBJgRe?6q1`D{%$S7g;b?Za)>wKe-'
    'w?aML!qw3F=txDbY;j<=N*KOVBK)=6*-#j+#!)vnbtM#1QcPh*ByI`?){XYGe@xk-'
    '7dD8_hf_T42HgVp<^+0(J_Rp!`@AR3Kw#TzoS?U-`J==V{%Yk~Y;uXw@d$hID$&%-'
    '<J$I_ZPJL!s8_(&;Y!g!U)HiZuc^9s%tut3;jr(e{Q`fb7yQau34(`CSmfz+5eE+$=lPo$~vBJOAHctOghqdx5k8-v7{-'
    '(6K{6Sg!-'
    'B$f0^LP8oka8Tlf0YCL=ng)?Xte7ses!&VkHu$PcaT4s`L+4`eO%Qs_d9g|eX>%o1*@t@TWvkJ`;6O4`>ygUS#PfKDMNgBGx<YSr'
    'LJFBWb6Jr&pAb==P!D+)dx59X_KGJcd1*&XpLvu$3K!&`O8Cm<*EGTEYtI5jJEj5sxwudv-'
    '*Uuoa?v3Veasmvs7+ojqf~`|JvXy4)%}P_jM{h`}pUz`c(d8#5pZK<74W##^;fJd|#1U@x2GWKWJB0e1~_zYm@&iJZ|S-'
    '*W#rTx9a<~Sl}(mJ@?7X|K;<2amGb<?Cl|4t6cD*{R3NgRooJ@7#{N&|MH>u=Tms%V`8fhTysmW4%wfzKDcF9w)Q@Zesgd3LqAME'
    '{_`YTxNYt$IcBfPfxQNczJ*izHHg~|ep}cbv-f5Tvn{(j@qat~$FEiV3NLas+plBx`lLVZ8K-'
    'W=2fxs<nQiIDbq|F<!h6IIw&ufr#2>BmN8}NI^kDqa5B<;&J>riZ@kfvNqeuMFBmU?SfAokydc+?+;*TEjN00cUNBq%q!XJ&#{;%'
    'PWPL&7cj|zvh8Nc;wi9eeC;?FgIv=tBdh(CJ7A3fra9`Q$y_@hVs(Ifuo5r6bN@kd$buI8N?v8<U}-'
    '>j_{Gyfjze6e%q@|5u<&a(A+74c)P8+nm>Jf4`wXP$Xx$;FkJJaJ~?@5GO_*Gn;@b<I=f_@}J-'
    '*46|ypGcA923jyoUYO#?>7T=H#Xr)q<xAkpNqsAZUWw1dBPLH&a&66dqxi^%k8mgVk-'
    'Rj@IF)0W&#O;j!E4@=8qYSbpO3+FUVl!%U*dghjw-MGS?VEw*oY78*Nk}U=-'
    'h%M%=vP}6uM{AqeV~ThVt8*rzg+h^YI*ckAl~TL0s;iSW|N=IYXMg={S)?{(<TzxU2qc`7hv?oO5Y+ul2opja+{nx5NR{gW*e9;v'
    'AbSSjOiFs~Xqtn)oI7FRH(C_=0*L7`na8O}Fyu?DMxIhBtnQQ*-ki^8diEVz-tLj*jTVsn3WhjxD&Xd6VY*^G_rPPwWz%DSnSzxv'
    'eI@*-ngh*5k82t@(E1f0^>H99*v+%8N9~4sNhY|B6kF-'
    'c*ccn_B!WOF3t~*|5VqHZ^&oGG?vi&6@RK4|caO)c+6UYr6IO1DM{*F&7=EnALjMHm@<<8~JsX=Z$+@R-'
    'K*mLHWP>d=B|V>$4B|`8M<YtmO#Whv#Gq7MnBd^-'
    'f<~^WV;8p37d>(D0jW&zgPlntPgq#?MplS@n4fxB8ncyyo^jq;Cgwa+&YxH<{;E47c#xDqHnEZ0W$94{G*_#Sbz3PRqXdefS)!e='
    'GUej_R`;QhBk}Tz4D4+w3#5zvhtN_!vJ}_5IF%;Jf0suWh$-'
    'f33(tj%BUiZ{fG*_u7ZsmOt6&$L{q%l;iFcyLbn@Z;dO5`v2U2580b7+&27RJ34oazxG&tKUU`Z?Xx{q|K@SDj72wdZj`&^v#a?G'
    'H}bh%Rs6Q}aUXWa%D&u-C-OD7<|7X}AGiyrwa@n${N`(q)yHG($qD%;Z{?qyG27S2*2;aT{Z8SJMqZ@r>hDVKLO!zivgOFx@{K<z'
    'KY0vp<=HoLexm5m*4TE+xVg{YUpdE;PwHS!D|o^&7(S@1;lHns&v{k1a=LEW;#2i~g`eHYU0QKF#s@7I7=7H*!Bg?t(%*gc-'
    ')9>Rjgtp3x?Yi5?(3YRH1Y`^Iv;Ek!;v%ZASU~8obBlvzj)Vty~noKA^v|ZbNVan9weuqd|@N^;buPFeR~b&`rUE-'
    'SRMaPkVE+08do0_yDDtq%<s+lL@TCiI8WuiWoM4<@6)(ax$sl$$tr$R&cTPqAH^2#%jbJc-se4X2)~Q9{loR#f;mrr_ODgHUEbR}'
    'Xis7C=-Z!ZKPz4&e8@PfWsxnON$k`6-~av|UxGWynK!e)oZuG*KeFS$UR%>2@FyRX$^SOvw}sh`PbPl6;28YirT*&s%rnn)E-'
    'ly%PVJT?u4amD>i>%gkk|3u?|ygZ-'
    '(XnI+vvG(`7U$z2JGg1>JQ3y9Kib){|1wCZbbK~`rrPxwLPene^YPgD2=)=xK;kGp660^s7ko3A!qT8E93P1g-?mDS(EPLk7mE-g'
    'YrlCv9Ygy@k3`n^f*Up@#}lVC$-'
    'm|voNyH8vmBFl5$qn;NKQZ(q5G(nBR|m>b(tHnJ?pqG&c?ZMv|}Et98_xzw!{z^q}}veZaxax-fXz-ai@!JO0Aj?t?2@__WGXMu+'
    'n|*TRL~!adg(KX|=%HGk<=-6tQ?)r!ykq3wrmvfvcnGUxgX>AX_v&kkzu$p+rCH^qlr_bx2`EBu@9hwkq1z0-'
    'c|ReLt~#SMSkEnm_peA}`3jrgdY{#E(6aF<)>v()|0b3JC;Gx12PaRJjl_FJ6HT0fkhKj$aT8h^%jC0FrYAO57TJ7*eY?h;*7X7`'
    '%Ums!~ty_bI*=j7BrzoWaA+nas3Ge-0Gd$`_BALTxO=*)r4{^JS1%R1-'
    'FoGBP>*xkj)a0Hid%T{fj!Bfv$S=)PG?{^AT2YmZSaYuXfaoIC8jSENdZ`Fst=A)<>SH5+te)Y_ZtYNGnl1IGy)E<;~JC?s(>tjW'
    'B#=5yL)qXnLl&v~!>CYiQ*oqJ1mhX9s?|4wYZJ!+Q$KSF$`}ntNbGOQKEC;cI)h)b^;U!Mxk50vR{@rXZ*EqL5{M)Ve*jK(af8&9'
    'D`$zKv$MQ#qFg)ZRJ>WN89p~4^qhrRnL;l($&fVI<XYBXe!RoFtSI6>|$NH<nzpc&Lr#&nOb-'
    'I@20nSrf;*YX_dc>%7A63pgIh8NkD(iE}zpeRJk1g+s&%dtx(b}0c;Y4yqMb5g}icdMz&mZ=Adb9pie(6E?tsKL}i3d5AKf-Zt_='
    'XSq%MX?5SU$btSI3oO&QCm%Us|if!XKS_MiPu+s6UrE&Ykhv($%$j?Ha!}W4#v3b!vY+P#4(UTjM~E_3OhhJn*S}%`yG+$UeS|cS'
    'q>`UCMX85s!QCVem(=4u4c*>`vg{j?&K)_@f8KYwtaBp4vm^kM33eXzlF7ef-f~`uik3*GBTF)Z833k3{8-'
    'rW_y_!&l?=Y;YajZ=IYcL|znJ20m!Y?{;2u-'
    'qk#Ct{vCoL%NSGxk5(HneJnY?>o6>k|QWwiR<~k!}BB;O3u)(ISX(U{JK@<`~_3|)lLqV8M}SCC13`>!be=RGF;$PBK%|RwdXl{_'
    'St6_Osc>tX8@7#O35b`+~m?}<(hLj#oxVyZSYOq5+}7Uzr&2%mdyD#(jIe;nwhh#&#v5C&B@W`kr(Z?mw&`BbzPui&ph)?#|tkBv'
    '+;VqmBURgLAXBs^wamnzu}*1eyuqlR`MSW%$D3a8`v!VyJK<N!jI0-'
    'ogoV*xt@=UthJf<d^q&X?_1eB*GAV`oqOH!x3CLV`*KCq{90b&=U(kT;X*rRg{NCM2DoW+XKJsUXWX%>cs(rq(qHvuSmJcN(!u!g'
    'y&rw`V)$4W9UO67eE$niIr!TpuUldY2M@O+Gha1w_$~Ho*tP!Nv(>q_rS^l_h$FmQ<3lQjr{Z-$5-Yir6K&)fJkR-qu`_HC{!)En'
    '^VBnWqttciO}{Ul3&-moYk9+B_bcyG`(W^bgV?X|mWcx^ezzT4R{d`)*lqD|mxpA=ujW)7+<(U`_9Z-bIN8}2jyS-'
    's1JOlzCbwDehz)mL`hI)<&bSrZ8yk|i#Ff~;%Pn2n$0x1v8YjlP-HLy!ISc7Y%}rOwIQ3Vb5i`1AFl_WrJ;!;>y>Cr(gXm5A++r7'
    'kSskw?UhbxjRrx%aZRPoy&y1k6`|?8_!fd*3&KJ0|9|kWnkH7PLsKj3_Wn76F*|EJ<Ph(R(YwZ2G8F8L{Et!2@_Cn=MRsGj<mFbB'
    '1!KG}$uI9bEOYBk6{hj#R^s|ipqmSJhdsgy*?eO9$<A??Czjd#9>|x`)7f<Yd4VP;^Dtl6Y<yU^CpL_g&{?Gr}5uY`2zA#L04&?x'
    '=n61gF_)X){vS%%I**6!jJbCb$%age9{6F`L+4kg2;_MHH(R`NeEFb^)$8$civyr<WQ`y$=NqOe7=Kllv+iv#7U^ZFCx-'
    'u83eRZ=9W~|2hg%?=)Zs-5_e5^&`L9f<u+WM^Q$#?E=$8fDZ54G<xIL-'
    'a6e0R&XO}e*vzqPWg@CiHEjqm$w;wx+Jp^DKOc57!WkKbRn|9gL?<Fk(K!*A~ITYC@I#-'
    'EIjYx^dS$SZcRzf?V|KF0V?*L3a_nf)=%ZqnyoKJB#9eh1|k{jIp4n9p$)yS4r~{lDxhpmTg!RnMwC2!8ai-J_4w!#8{guS5R&xe'
    'cyryVUvn+&@prX}MzmZj~wf?i25^g~tQp*D-AE(=n`hPBwJuDE?-TFZ$McaRrluvab!Jb8Gpo*04LqcfSw6@wv8QV-MnYh(9{OXY'
    'BM_xK%wm#9MFW2dwAR)4AkXJAmJH;t}S&kN)SYuRPu0kv4U3a7=gQ+Yk2d;I}r<+-'
    'Fz!;h7kcj1l<n%CA)ns}8YyBPMHS%~9KWtUvlakM!?H2T$VPg5QSioVmwa{dG&v_hB~2bETd~=JvZDobFZPRkq^PM!ey5^!Wgfve'
    '?13IIVr$`hjt0>1WkGY+ZX7PCR=Fj<xsnB=y{iaZ0=3g!b`w71Lo4Zee(A4E7Nm=KZ(7{q1M(d*Aym<?KrS9DXYAefDEN_G6dwUb'
    'W9|<cA^FtNbBkyzl#1@igKc!~@BfMZC9v-'
    '{&};S@<4jNp3pvBJPoUiUHt%6bGP8L@b5!T7&w|_3gL))%BkJ;SYa!so&V+ztp4ddpssS$@TmjLp-yuL8d%Z%l(5@jX|pS2!4L2y'
    'vnLh%1ihG;R>r~pM7?T5803f=YeJFzhIVo<IdnQ+OEIn$A@8JEplDMtk);?s4{T5YFJ&Jk_T|e<*56D*P4!1>?(fA@s#)ZKI8fD^'
    'QhC3&kjZeE`(mK2^^z$@Edx!=wHQ<cps^FmA%MUEBX}Nj+I;bSg|Yp@n+85HSfWn^H+`BRlR>CPAT=p14NgCSz^|<#P{=cemn96F'
    '8Jv`{vUZBZ%W>-'
    'D|_9uuhG6d;<FPm+l$|tt_8cyt=I6YHiN#g0c>FUX|t(kV*c1L|2O@+NE}nOVftevHZ9obkHMQACegWS$BLeHyT6f#Wx?<v;22rT'
    'LJ#2>y!f<+UEZ;Uq{eLw8>r5`uKFm<^jBDVZTNMYuKsXJKg+Xg{?+t{5yN<^e-'
    'u04>j0Y(r?s=^bI!w5^$>P<l?lI#R@aP^OWUg>JsGyB_mRZax<;N>?X6Dm9sR!7pKh^l83VniYw2GVi;O>MldAhu%+XT*szZ^rec'
    '3Cy{Z?hZ*NJ%czElNfBcEdLKgLti>VK2`c8M9x*fHX5u9C+!c9af9x95C<k&He0e*FGw-'
    'bcI=OEbq^-P&7xAh+M0@SCn%<{5*>U;d9CdX0{?y7h9^u{^dKe$j>UjLq1;c`OfZ?e~3OWX=@G`i_je{>vU-'
    'bJ%@&9)sT@JlCZ3<HZ&Qv)LA{#GY4K+GMT&#5S$v@2vQ>=Ui!<hDG-gga_eYo&AI1m9lpYj>%(lYVN5KPk0i3lYY#3vv18`=J`^^'
    'Yfs$ZBEfIU0lM@DZP2dk`zpf=#lNuSPtE6LAMa`|%p>C8j<S(^^mG~D*5=8zp0)pP<*(akqt<LazOt=LI~LKmQ~js>TKo>~{UGr~'
    '`*2#b3FEs(-|E_|&e^wgcq<O%P`t{xF8Mik^z9h_Xzg>HG2cRBZjQ-^x`toHY9%gs&5q7<<6CpY`JUC*o!VdE*6OIw-J5-'
    '(55gaL|A|k0Vu@=wHIHKYamM^(;)nCy8eWI&=ZxRJ*u3E{>$o*Lb+7uP*Epn8@vAsyPkC(Ou{b_R+~yWO$LjGB`6oMe$+foSzu)o'
    '^-'
    'hn^b>CdNNbeDXe^Stp8Ui+lxUxZn3(_d%5`__Jf`HZ2v@JBd4bDOnX(hrK+%!j1kR{ZwGR2~u6o4%TP@V)T8`}8XDZS}0NF^BH&P'
    'd)R;y%M9eFAj5G{LwM>T^mp9Z%@Im;+9yMt=P5|{FZga9Gj8*X^SmBZ!0z=_X>^&@VGt{J3s&Cm^ttXHe<mLcImUn*sHQ8+i8PQ@'
    '9PrZdh}UmV{W+I_Za?lp1-ctH|1IIoAW{3b!-'
    'ZLncE#>uU2AGZ%JvBWnFws3={nPX53>{*N%<(uUPo)DAWC~|N5^#|K@N0=CilG?QLh@^F7~l@$9qDUh<psf40xgzx7+cwSWJPcf6'
    'zfVLtSs58Zs^BOkdLzTPWyZ)+IqW_~U{KG%KlgCD$fCQ-Xrf6ov0!$17P*17kxKQi@f@743hZ=ZhpX}{}!wfDaFy%+qh-'
    't!@n_WvbmpIv_710V3rn~#3<qrE)IFUMb&=eM%>{;GX{t$kwyvJcbRg`S!FZizK!{6u_ro;Bp`pa1iJ-'
    'Z81`U9ZEJx3eD3x(;sb|J?Ix{Pyxke&k1b-5O54ZeC#--'
    '*FRIcOL=#Du)Y0=W+63@Y%Z;fj{hXpN37xt6jIes*Cn>jpw$uzxcr){K3n2zx&-'
    'c?H*TceM;B*^Q?C~+rB|Msr<&z;It3N3D2wIlUjUBl|PDKFXOXoH>CfD{%LP@^82wbuKQg1Q{VHR_gpp|a<65r8~lboC?DLr?$Jf'
    '~X-'
    '7KlzVRh$vxZy7zy5sBhH=w7*LqIp@v{#&`X0SgcKB`K6kO}NY`R80`{zTSc5umO`5f+hFuY1`qLK%>@6qI!edd{G2pl_pbzeu-'
    'L1&u6hwm{ump%hKpAUWPeF<*98+u9CJiG5{&7SEz%X46fvuDrLYm3`BMh^#mwLjj%q~agHVRX1&6F-%@s3ZH6ep_u}d-'
    'a>^>Z_XfK=NbrN$Q7BJ@wSZyWaIK_PF<5Iv8OO;MhLD`iY<TiR)(9?^WE^@^72d=(pPUA>nrw{MK};`U}>ck@v$7+Hqpr>6)=<*#'
    '7<*99!RnO}FE8Vb1@|HrWHIPr?x9e&6hB$4mP(dl2ldTKVDD_r$=gj!V&NxOtAbc-9Q+w2y<E`|TR8?3+Fijx9dU^a-'
    'EiJz{ePr_r&F{$*@p<BS(<{urk_UIcbNr$3(8?y1eX?+=Exe|d#N!?4#?Iny^hYqVz{OU(r{9#q`ca=yn$80@lcJ)~p%csRCN+Zw'
    'Zs!P<3<YrWsWz~|}>%k&xbulhQ$?D!f(U`B5;R>CZ8FvNVKV;CHUUD~O4*2Z*a{NLw_aLyd4Vn6F!`)!{un&-'
    'h{%}+n;*UVF{`Hw6AL2t~LNOT5f>OF8=@S}Uf-'
    '@aoDz0W)}oCq0XWVaDMX9MOogd=+>r^H$=_slt}tnIZb^O9xVreDv#@MHOnV|ZZwb>OtjrQkFR+~`@>DfvB2U^DZwb#0wC^gipyT'
    '1L9q^s~=z_2*M_Bfva<2WySk>GX|5xz+B<zYSS%8+NJVmAL|J>fB|vsljEdJhjcMzDC?TZQkBrx7Wp2a|p-'
    'yNnvI!l{uLEp0bud<hMV7<$_t^krrFMW)CL+{Wb244O{cgW{k`4-8<v`nD^}XR*yN0A-'
    'L+J#*ud4<sM#@WlK`lAxH7)hwvL~jU7FURDGM<sNxr?WebjzU;8?1?{N-'
    '#_tC&@9zTu|;|U!MAGL;GEnmtQyEvEcMC`)9E!fR#z{-al$set?d;dIKC9J|#X5R52XLpA;a)0f)rFTPC`RP++*3;-'
    '*U0=*x@7y+b@EI<87yn1ePq$a*F?WwHb{}l<^+nGrjtBQ2oXDTwTAyw0m)YW&ws@)1-'
    'b<f}ok|`hSeCQW7oWYpnBSGN*6$_XShbUx8^%YFT!G;~=G<rxBR}dIj<fEq%^BCmseSkrU+t2^Df#DWj-}uh-'
    'O&%*v#ztw;79Sl&*yVc=6p>#^CS1tZjmGW!F$J_wcoGJv)4HDx!-Qc^{j7+ABqn-'
    '^{;;V`g!#?hl{FxaoEvCk6}#U3+Iecd483Z`X9pUAf6d7g5ip7+iQPU`p3>#9R15{owFtP<esy2Zs8d_I{Wu4&Q<42&geB8_`vvW'
    '?cY3hTv*fZs*hD?(%;gz);Ny&|M~Mdr(4z88P5$JJPDse^*v?p!5Xi=@BYf4I)>A&x%jGHRlaRY-=d#0S64ab{3bHvI*-'
    'XSPRFeG%4d)GqeuMFBmU?SfAokydc+?+;*XwZ{s?}L_@mSKqdETV5r1?Ve>8pnh(CJ7A1!&vAMr=0^GEbdo92Fx_@mSKBXeZ;*y2'
    'AP@kfXGqxc9O@kfvNqeuMFBmU?SfAokydc+?+;*TEjN00cUhs7Ul#H8MT&1+uM<<+l#_5FYRkN@%c>tFx+^EbTV4d-'
    'us;~Tqt?bm+o`CH!dma}j8hHp4~>s#M?@$KLK?H6x<``bIWz{m3R(@$UEoxbxszw_eBC!f6dfgkvR%Xhx>otIBN_0%N}g3tZ~ANa'
    'rxpG3Rf`ePX{v!1|3$kWG9&rkZUcfG6gNPLJ@_=<*)?1qoN-LLzDe*DLOoc}aFoo<V)tKR?q_v1gjUbSnko2}|`dDY*|K36}?%yY'
    'P(^}ltlXXUvc{NM-4Ib6QwTfU{&{d>Rnd*KqFC0x$F@f*Lfe-9VG<BL&N_fLCSNApW5v*)<RwVnkxK4QZ6tRChp@ejxE)c&U<-'
    'G|0sNZ$M2_g)Upr2o(NTFW1w8~=kGD1$%fYk6&kD`<7@V@o)z%qP8POX$-fpL2Yju=JcF7vJ}N-'
    '`9QWb*|^0{CV*ugk!05?Agb`?+Q2VJ=$i$j$ZkWwD)ZI4*wS4G5!dL1t)D7J*)R}517Sg1Uvd+{qCBkzc)?)ZyN5McS~DU|0;dg|'
    'CQbPYoGsg&Hr4ui;hivQuz+H%2a(U>HAq5&whUEXnq{Jk$TZnpQ|swV(XK=FU|Z>gbp@6>HS3Ci=KsVR<6N0hd=D)^y=BT%J$m*I'
    'Pqi8Jc#w4yu9h}cge#RoZ`RB=ap}p`J~KqDt^_EA1+3D>N(W7Q9fFIu=Pi}<=Q2e(Co{@E&6?Q8FsB7be!0S${)4w`scVxoC^LZx'
    'r?^=Bix%YW~^EJoUzEs7^eN!@S1%wYxq|iG5pEBZgh^oVQ?V5FS1E&AUj^U#ac%k9Gg1&qp|3wjUQdF;Ysx6cHgdV>_PNxAAe*XZ'
    '~Qe+7{0H%?z+B94!hbPYJZF$ejc}{-'
    '!E<EH*65w#dh0=U<~!zbZ;3;)ZKX5bjrM8(U)3h7{Jh&1ovjky1<^!;VZR4`l;*J^sVwo<~^`e=B!sT?hf5p)-'
    'WfCdUSgijv{^9XY7OTGcTxIXZ3Xro7wGE#@#UnEO=&IVHe#K4#vjz`?~+2+QRq=aK+anpL3Vw1(@}%Vnzyo<T=Y)uizJ*Th`bo;<'
    'wau?6X<K|6|V9c~*Fi&%N&KPsn}{<2Bo#@i$|x>tn;TLBwYS4~IWu6K5>qCyY&t&oFt|X8Y;Y{MuYu9kZUa7OJ=%D~Iq)9gD46=2'
    'c_dgh|&y7)JLpUTas+iGL$l!e`7Y`uq52!|z0I-FJ-By+7ZPKf0GSiLzu|2yR<)7d$7~(YZSBNWYEV4BVDAPjb(h)5q^o?>)-'
    'C*h!zopO8K@Y-fLu!)(_a<d16JwXCIKp&afpuOVmu{VcUlugM|&G8YJL(X))p^Ef-rDHlIoB<(s&#+l69(r@F}KbAj=jCEIUyZFC'
    'O<d0U%dZPYy%z|6SiP*H2`S<eMU{&o)@e$2^q~B8?jc&p%XHjqMCEBNd$yY=N-7mg`6ZoUWPn-JOq5tlTzg6ENWuCJ0tcukd2bcf'
    'rZ`ijw-^e&H#>$g&gjM?&{wNsi>$mm0ir=v^>FG{iU7I(Tx#dy#?JIZqqwtn&-'
    '9GLpxlm`$V+})s8>s%jeY#lt$6X}&t*tpSpRAb8ZII_5!Y$XtmpS=97yiiW%pb+BC5KyVr2Zbv>b@AdoZNME((fx)$F}tv&Re2g3'
    'V(EKj<Yr&+OmNaugJt7b=?cc6JE_{)vup5RwU01{?*?<oe_U8V{*omi9b4s(<#`IY2ADfzb$)^XU}DT$KVoI`J>qvU%8?!+n?*bu'
    'GyB#Usb>K+C7iKXphX}?5+987G4#%wZ2jHd(NR&`H%2LYkW|}(X%qwEcv@udAf>Q_9et-AES5kSXlLU_WM`tG7qk{^{#efOJ`!=*'
    '7%~TS2M3x`{K+gR}QrDzNcWcHqIQ_3$oaj=>IX}&Z*cXk7Ddz<tAs2ZRU{D=VJGUecQ=PSMjZUdF4;Tt*`arL+g}km#S_Jx&MYYy'
    'y5;E-'
    '}uJ+uYdjP@4xPKue<;F<B#|Ek@i3S==`7l(|_9IkVt!f_D$dPP5u4gN6!A)Kl^8AIHb3~{q3Dk`u^|#ew;~{cf8{r7ysg4{EN=53'
    '_oi3ZQ(SAf2;FDK8x`C5&V=`kop@O(%?Z7hqU;r<L9X{HrYeW|7xwk-x?01uCvxSkg-'
    '<kzvUnBTt1TFhrIvV*S>b);M)81H^2GKU10WgU-xzAZ++`qaZKmok)C+si3>RJF^rg&9$)a}lTUVB5;qiVYAljE@=3(EW54i-'
    'Y3RRkO|JLbaBjgg_p6+UdcY(8w=pN{^@Z8k+q$|Q<<mS6A9EFsL|xra*~7oI=fdagJHF#P=tqxvQb%WXh@pDtJKx!L>)XEV+qC~p'
    'Iag@er<+)cjNv}B*IoQU{O#IJn?=GWl{kcsMdCzCtjH4Qmc9K0=YGB4MwfyCOj6h3*V)mpLvaeH@^4Ldx_>TvfwE^bXUo*_IXu$X'
    '8@|lFvyWLj^U?5i;%SnD*}cMT*1gt4KNi3Ih`*XKT|TeeTkuIA9I;6^i5D3DxU1}MoVkWIZemZI!e;!3dS_3!@2h_^{UP(~`MHt!'
    '`}7q)BzC^|Jp0*#;h*6c9gKbyU-yD@@C;{}z5iLKhkGj=cd%XjZShskxJ`SwZ}~yu^H{@i*3IygYuwvD{;l$GGap9>%U;udCa<!<'
    'DfSx&LO;|u9B#0LWArk76q)%qzmM-'
    'D{@V1__~qBu{dHb8@A1gIXDfzb#<TKAssGj<=qdJLr!Aug`q8j=9Vhyjb6Dex4=+*X#*1x<O*D=gFYG^PcDeI!+5ZqdBiaN05%bv'
    '0+qdSy*~eMee|7E{KKvNj;@_&?&HIGrc%2b{(78*teauI^cEL09mA3mV`=6_fn78gfF{gJ=x);taf_oWU@8TnmA2w_4DPQ*WoYOm'
    'g3;vz>5EE|`|Kad!9fRLZ{PeLU#U3U8ZRsQ7e`=qN{Zn5$6Fw>&Tm;`X<{1lD6b>l+i7HQ2KabRyu6h4%^(n%JuV(V?+^c(2=lxi'
    '9&ujHh9m3DtQ(a5!+pY00F>m9$1;aV!A$y2iUpXkaX`|RF`ocEBQQi3YX8+!d-'
    'Ik;c^85I*vL8Ba5zeH>IlwIZ*Oq_uQ2avpe0C*s!z#Y3bI>}Eiv6qnTVjFBymN<t%a}Ljxt;SF9LBw4&qmIkBe++oe(RjoRrhPwb'
    '=|T4(-Zikh1*V_j;Q}QU+8*{9US9#bbWbl{EE~5>RapVvBz@pi5|-z!7JQb*5!0-'
    't<HPauMf%}&GBywewkxezy8d@)qU}?9~&I&g7?_pxLh0G%-R_tht8DG84I)DaLs43j|09VcGro2t9);bPg~1JQFZ7T-'
    '`1KAMqe`bQuh&?uy7xVv8i!3^SKMLf5y-??(G;3_*nhhxb7z0<-'
    'ESG^W(a|<`nKD<%_Ou`Gu=*wZ?MPd0C0|=woRaTX%f*r(jphcdVa%9$zvisdMPM_Smvtcjb@fIoUiv+qdt2-fO-'
    'l^M3nd%D08#yk1$^_pv!=t~$3e4?3w2SN!I=?3zEd`Z;HP+KP=?n=6NZJC<YHHx5^QDc2tz@4vO4Jfw@}tZV-IeP^Xq{MPuwishQ'
    'UtG?({Y~aeiiB<ip{Lwrod)WBRdN<3gH*5IK&#L!b<0gaQ7U#B)f7{Z>E&W@YkL<IX^Eh>kEv!0mtjy!VyvL?;aQo&iTm5h!AHFs'
    'I)c?o*ZrQs-&p4L9JO#To9o*t3Yh2OVHMwqWY*?$?F&tgpD>L2W?7P4FyF15|cpvANKk>v9_h0$SSKj}sullO{U-'
    'LCzbN;&5y{>a1I1oJ1w}1P$pMC4MerxBE`2WKvwbvepgb(ogJ>T;^Jq{^?LlT?B2k%+<A-<ZKKk_-h6`qCUcRo-'
    '4y8KS8lGq*`)%Sky_x5LsY4Mq7;$%pk<#Rdb#0%lN-'
    'uAY)5%=%$J@Lau>OSW9%CbMct!>X=^P1NLmmY7_u(|)(V~@eF$8o*sO>a8?`mg``jt?Hha~tM8U*LCr*LV4>zl!T>m|lGIH-EFb^'
    '!k7Q_kVw{i}J!i+4-~NC#t+qcp^EP@E+NF9?os>a7*4ld&+SlBp7=h5kC`-j1S5BAiiuq4bQLfUu5LFS$s)VvW6di-'
    '^E`L{_Pd7cm+K>hgZYx{ME01b&r7)_tvoMx`n5NADrnJtQ%(iHTu@@gHQKQ@#EP)Z%r6o@~ZCYN@x5JpTufKuV6Up8cdh(2X4Los'
    'dsp!tlh&q)cjmN%NlFsj#~Jy8Z)})Uylx|OZIjbA8yyLhSeE)^PAt?vC=mQ%=AxjgSg9vS=TLXIC403J}&;gcE6pxal<!f?GRr?$'
    'Hw&|Ph0;TJYY3+XyJ0{SM+Y^<PLT<c5rYtJ-'
    '6E6td_l@*@Haxeq3eUoxKBPUu^dW83%%Y{7BiSUH!LB;Dq1q<x^(3%3~#WQ>#mlk7FD7K;0vH?f&Bo>4mqWdt$SyA9TcJ^fnwm)W'
    'ugea&KOZ{GZ{KvWK|)HIym+ti}xvKJKde*3>t34Yv|sNc?J}k6sVo`*nQR$*E!vI($dVKJ@tN=A4L4^og#c^&H_`A08(D`}wTq%z'
    'eCf54s>mRcwn`suF|N<5OLe*aq$4*`+P7;_I&QOA%OT`{>im#m2^u_?q-'
    'JF(zF`yh*=@*d2N{#_=V7arj#MoWJf(4TfvnaEYH>#+=F#&ikR)ejgo&U;0z_>L+eAIP#SwFP-'
    'b?VPb5;_0q5O>+o}Rk9IiUx^7QAN%bXFzex6958Rfvt$yyr$I-'
    '=_Q=!V}+e;s>IIZaC4ktOszRmkqYmTw3t^Lk(`ApV$BRo4Fo;HMmen(FdyTsOt+oIR_Bi}WAyM$9AaP~hLHX-'
    '(;>(bbRlz8pM?;i<&l{NE`u}HVLw+;UCy6&yqiXkNI82zC;;lK6Mrdvzg?~G#=c&bNyf_1$Se{=fP+I%-'
    '_?D!394!rv8=vwyEWuKruh84R5@kqCL@`_7x?q;pBg5#pc;V;cG(jV!L`ItG0|HZC~myEA8xe?<Bo$L6pq{e(D_l)*Y_KYFMlr^0'
    '@CjKMid)*h2@jByS_)C3d_Op)o>7KtJd!tIs{xZ(GmwuPM2XaA=b?dz?|NS9Z<2bWlf8?Ot@v%k+rv1xD?^mAv_lb)i`*xN&c47x'
    '(XEG09%e7bS!!@2i*TgnuUR&*W?5XnVFUG*k8-u}C{6~%J!bhgx#-'
    'F(6)2q344((4qHGZ(hIcMCbADJ(t{)0<e+ALh<9RD_a5IeamhQ40U@k`aWpEIkgZ$9VC&+!U#><qkWY+m)d?(>cA@yj2LU*efFPn'
    'hQjnJ1`!{Ar239COy|wSDLN_MXq>iyg{%>How7#@^2O*1UoAa4Yt0*27cz-XrvHXI?sE7h4xytK-KOU$Evo-'
    '0~;RWtw@3;HaId@2$*9cCg#$n?I(FPsDF$Zdz^Bn9J;}1?ygieX*AN+H(G^_W$a?tiHaAXX41~+@|t+Tm0o(+ukAGd^LW*VmI%{n'
    '&*Ir{L*XfTz!)jmo=IFr*(f%jk`ORSDIr;=5n5j**t%#d(f-TtK@jCa#XxSjWL|#TGn!aRo-zec4qE>hvIcAmNWia`wn7vXRHqNs'
    'm*<-rSI;@7KgNkU;IQfXMRY+TkMMyTZ`qLui5(k5TA3xUZPd*cWV!7U4I<QFCF4Q);Qc6H@wAb*ZZ#R-'
    '`mHLpNiWa*~DsXZM%izp?IZ39MT&1GuJ(OHLrcw?BhPnj^!7RlpYU*p9sGr*5_UCdRO;D<2K&%mbcvh%CG#&^H;s<Rp*aC{`eW6K'
    '9SSz>%Q*m;;-($d>jaWKJk9U+jRZ||C4-'
    'nh10nSkL11ea^hxuAMU8+!pk+;8{DtKf8oKD1DAjk@?81k<l4g%`F?OkUHp%OAg*zJyHDRET+ffG@d1&-CG~o%A3yovWZ-'
    'fC<u8Bv{jd0nuQ<oQ@$JJZ@mb0k9uCHEQg-}Od%eVg;flm0B_H6xt*?hu|K#=Km-j!v1HX-O_#AG*8^-ojhXaWOYxwe`!#g<p-'
    'u3l)X_xR#;p+I<TRHk%ICGE69|gn0!C7;3y?XuYU*9ok_~1a!#c|1{_`27<uIm}zDA<iWf&D$a=&$$fdu8W`zaBXbdcH5%C|`I+c'
    '^B0uk~*fIUK1lj7YFxtll|zyIQ&`mR|n7GH|z6<_|o}>5|<PIx3&J*lYA9kBKxJx*Nvay<ANXD+?(%%;4kSI{_U&3`m1qoXZk38('
    '?{`1IHbW#Uf_}NZ%zMtzo2LEgI((nbfEj)sxNQkSYP62_$A_>kB^zahkokERkDXa*ao}cH)7xx9}!II9{1$qtN!ThH;(=EI?prM_'
    '~4hd82oSoS?@OK_Dc>*9B-3uw_rlY=w$ouqG8y%H+-'
    '&ojx&rp&y_Xw$m`VkquKw4KN|k6tKbF;Wf@$?!dHy=nXHR$<<P3QC6^S;;-{1|JM-G?r49F%ai;o6!-LfQONr|pI4-'
    '&wZmLMfMSi%Er!X;3oevx581=f2^T3w9S~*82b38tK&lvUYK0W@E@E$ms!5>}0e{h~l{k>|}*ck7_xz-pESf&r<w{^W9?oC~?rmy'
    '>u;gxf5;?u93EB>hNqmC|CEQ{QXGXbx(Tjh|G<0|KS%=uD+-SCz4wozt01!;A-'
    'b|wn0ruvkVV<f&?zJ2_L+>z0(=qJ0!PQhc%#}V98AK&Hr@F=hjZ!+R<mONWEA8O%2I<8y(16UTRXOHdhSrf0c%&qd<nLny_BKwer'
    '4emJO;Z}U>*NG+1UReHG*coTqnAmkSoKWme^|z%A@s-o>Nk6-'
    '9eyk<CpS#BHRDW&uQO|Mt`}mKwbMhwX7(|DwZO!+=wC14A`_gB7{8r7cxhDFLdek!n@N*=bQrabP5^MPu(l@vGqnv+O`6ItSl|Pz'
    'uccyH?B>v`LSJ&FrHe{|44uq`_2N14YAEgiOK@XI_#%<M@p;Ne_W3P38{WkoOdhX+oj>&%&n^^ZK9MZq)O9-E-'
    '9Wq|lxmbA25mOmEca=P-'
    '+4GTHVyEW+s~l3bXYu#ztCc^BU*sY2M~hv~+^EFhcKgB}Wo|Y0R`mT3bw5b>H+IK3KE{Eok?(mY&bP)Rj`>B;V@elmJmInV!(h&*'
    'pIC=^FQk51c$t&=qeJ`~+Z0Yw9bpiDzw-Q<2Y4O(Z-'
    'Qa?r0c|QW{p!{i;s4P>xqwsZ4Vasjo7W|QI+{TOIVHki%b5sjXZiM^GApDFMC!Jk6d}T)IW1jWsH5!SU&S_DRcJ54E<dCfAY-'
    '5|5Nb3#s_Pg+&6KWV_(|68aosI$b2Jxvz%G6<40ZFhrZ^&x(oj?ase;6)%d|OzsmT!^o2UkY;mhca9**wOB`v<$C)uU<5=`H_niI'
    'pGY7J^7y8s#%R~6h`@-h^O~EcYvBkgb<KFi5i^{9SW*xIvel13#?!lkq8jj)N?!q6{HBLRtEaPt3L%7V1?%?M>h-'
    ')yZ9LT=7$$j|EoI%Ywz7Myx{Bx)BZ)<Ch^rehp$M%C-'
    '*DaoG)|ok`V@+>n47XyC>NDo}+9`+jtvT5tjyw3x`w%Doa_PHu{(OuMR_<*+Cu)xOoAauz@n&l=NOQj0`s^ATyN`c6Wakd>>RbHV'
    '&e*VZ-+lTQzsy>E-&Vf9HNJLV-q1CEZ7sjc%q>0W{IBTi%)MPtYmgm(L+!`M+O#dMdn<mjj+gu5&}JRn7f-'
    'Zr9&p#W^U$N7Tdu^n^gLqz$0s<$=c%Wj>iO9I$v^ogJvPK^&PQtRJ1-'
    ')}L7uU}ANBV>Z`Yi)YtQ(#+xzbCm)9<Q4w36__#itUfh$oKTn6FyPyCYi`7Auf;Jy02Jb%RTbk2cKm=7HX5mB!8UH1)>@B6;*>+u'
    'JPOM2poCpr&O&s19Dj&e@7^X+SVP%D!>Y~eWIbpIdxgMV=TkN(j=>aj|&<lj%(;@=PN<#%53C0@f%!9}hzIo9w)Iok+tCAS*?e9r'
    'q$d{Q``2>-tIb@GKcV|<(s()FM|S39-m_VRciJ!$3WpW)`zbHsgh9;v<dbtjw>%bPWAmBb_A-'
    '?W>uCI4RgJuL2j>6d=#`ImqBmv?@t;nv#@2g0}CzVC5xuo>?c9#9)R^UO0nMy0K1ml&DE8{sk%e--'
    '|y@?_qR{9!vhrdPi3<mZWB2gl^Q8fOP*zUy(`eaAX^7lXI5!WWl=yWxX}UCo)6J&g4%gh~JKY_RG2BmPaCATCKf7yb=5qA%!s+HL'
    '6TP9IDhmvZoV^7F+%YJJ7GEgxXG%j8(A`HAQu-jUCFoRbv(VBz5WHt|PfoK3cH$>BDw+3Q?3dusWBa(};f{m6H>oMSY{6NJO0liH'
    '-7jn#hFaf&qDI{&6$4n8UUGx3(4=cQ|KgPHeql89q$cA)#nE2ogNweX1H&ITX3@JEUHNPf!XLmGVWPTX6S#39w#s`!PI@28#vLws'
    'iKXuL{Jr}*sWbH=9_xMjUIq+>+K1_!s;;K7Ao41TV2aPYy=t4q#X!=WUeDEYql`1k`RpS}NkF2%%kz);;2yOrFB(G?iZ+-'
    '{AV^jV45xf=VRd;Ce_2*X__2T(oFdE_cv_F>QS-'
    '0ZWhxs)oGKKQq8SLuK9u8urbz3;^CCpI>s{ZbbEuDHFS=N*IA*Sdey+@hW(21gu{7$ncqhr*3#uYP#$%JbGU;F5oFoTIdGNXdi8K'
    'ID9<<Y*k6@8Yi*d1<cWQ!+2*yB(ZJ%DAJGH3#CD-?1G_{M&rqZ(;=N*^oImyzVCo&%r*>ms0oc-'
    '_fp9PRfp>*i83QmJy$pJsAsMo;bt!h_cqKxwT@W^r^&y<@d&f!~%qS8a!#&IX<!YuWQ~h+<)S@%9`y~4oYQ*O*qJ`;bu-Lv9$BKQ'
    '8oT8b|yIk(+(pqV9vI?Wg7>N(etKO9(nM@3zu8>^TbD#dU$r?N^q6Y&2s+LGWQ>Osk{HM#?}=7Y+qZhtXpp7pWMpVIqwIoIoH<m6'
    'NN8MOmdCcG!7W^#-'
    '5DM$EEG}a7KOX=3myA)JfjT`HbbYGgotNGahgJ?pB__DR<*_jZ4b@&12$^_Qk)|yd24IvX)P^#v0c%xH1;Zxpehy{H}SvJs-'
    '*nhsp(o=L|2jCUefkV>vkO5WLbyvoHNr|9w6GF1d(jZai_n(-'
    '{rR|LOlZKQCiu=EUJL6IVF)X7s*hu9iIm#v5lyrC)_hTZ=uKbFlI2CuY$9@F6)<WIhu;zT5b{kLBOC{D0NwT=}=0U6!@W;E%3m{w'
    '>^P;@@&sZss*P2hKe+m#F)Pvrmkj(uZ<3NMexYvr;O4`YD{~PxWntpPsqbeLmDfXZFnTGxfZ;+Sk(G*s3}HZRE*bd^Cws_kZ1EnE'
    'gGOf59m0qB;h}=UDSSh;`;ii*IG*2<$l3_^uMax$Ikr4XZxDja+L7^DUineqQC@s^om)>|076hJoR7eqQWj;e~1(#7>;du=Dkrex'
    'K}pnthD%#}1yf>r}>ywVbfkAA87u|Df@M6|;GNQ~LFY^WT|EmYCsH|5~t~ze_#iza6p0JA1_E|L6Q(YcV-Bc5sb9TEpx_?r0uA7o'
    'AJ~>DeAm@o%?spU<%j2l%38?w@?*Q?8X|PgCqdJzsW<ldJyNH9ze>4s-'
    'U$Z}j2K{Nr{1M)n!jIdd6zujZJAt@0cbgIRpT%YE1Cyww(KJlsBxYK=ci{=R*A`{wflxA@CBhATFGKGW>jT$h!5sC-'
    'V&j>>pY`<%~>4|UEl_q#d1Xf4(wI=RLl&1VG6>#<qCW(;RsXT4k5&$c5of3(H#r4IG1t+hOnbNt|(d-9lg#5JC-'
    'V!V$(nsfSZogY7)vAlVHz=3=(*N5<1I~#88T&6WHZmq9v#aV5gw>gh7hxTq9uz%P4Z2TVn=;A^7BmRE;5r6C{{E@OmDtEMpKe{-'
    'UKgxUM6N{ldl|O>PlTSX`*Xh~Iz7=~k{P&ALKKzmY@ha{c{^%e6!+&^)KRT=YQR1R1e>7rf_VP!`!;su-iSv3`{1L$)i2>pZ&hPL'
    '?Vx?MJcHjRv2jeRH!;ayPa(0vaiLK6^JNmLO`?8+X4sL}%IxGCq!Xs7wh+m$bi$UT~kkc>v!nZg4$uob{|F_=bS8ezl<d1M(r|?I'
    'vhqv~G8SHR2gkN2`AA~<@_oPebuXx2Py1u>kwXZ#jKl0n5Z=L_JS1&#&e#r1g<4lw_{;1arPC2&>c8Mh{`4eaUXu&V}7mwkOY7E#'
    'oA85%5_@Mj|n-=~EcE|8X={I5r!ynD(q*VS$-Q%+#zRiU{N^Dooh&sd{#h;&bl)e`n?!X^i9pI00Ucf`+k6Jln(-'
    'uD!Uo&6SlryaJNBWa%6BDU#<;;)~1GU8Z9paCC7w#={{X6hS@!8G%(be<GA1Qaq@zgPF81(tW7JuZr<jB&ma+XVcKk<i!Kg#)n(L'
    '=tW;@epI+6I4gbw~c_>iOi4lDl<qNPGDse)E|>O5D~8e{@r0O`{Lt-aLQoe_!nEL*|dJo-'
    'h8$`{byc`6F$*!XI6y%}egmn}^IFUG3wKat07i@P*DFjeREFJ|5za#K%3C{83^CU7vAetQ)T$B7b!Cu=u0Q9qe@(`A--'
    'Ba^lo#U7rvBDDfC|fA@39AKmgn9Lpaick$SBag$h`@JF~f{89S%Dg06RqQn{=%O4HQZk>;?53ec@n?K6>Drcb0{LwhetdGAle-'
    'xhk5PvkEGZp?Q=aJ3%^y<9iF8fdCF{GaV_7M1^t2O>;tZ!ENqj?Ov1AnySHw~V~pV<A%AI<R#C-O%J&(E9qqnji6qpN-VQO<K*;g'
    '7CP;E%4h_#?lov9&pazUD93=YO7bZ`EH_{8I<<JCQ%SI*~uR+QT1R?ctBEw)mqp|6YxAJH#Jt<Z!yP{zd2R$RAxjhy2miKK`isQE'
    'RN*8V7Pr4B@euJs^K{^&Ig>S6lqiRt(72SuJbv5&PngX8l{6U+j|?I)Aj4|8MQg=zZ}=8!;uf&NDv5AI)+H{^;t3#2?i>v0LX%)t'
    'srbJ*n$}HO^-~w|ndS<YUhZIE3Hx$seVS*5cdh_gi~6*2a!C{o6CI?tDy*pQ-#!i9_Pw>V9YbdcIWt!f-O-koXDt41Mo&et*8~SH'
    'AL<oj(%q!<X&5H@)di7yOO<ir@Ba-'
    '`0KT$|8>(Nq(&=`E2B*>+h9ua5dc*=NWhgzTV`eQm&Lw>=FMapSfqdkLQm4h<(kJ_yBA5>>HlXbr`bX2fO5&OP;>A_JSFo^f?Ym9'
    '>B*Qd+h9MzUFISb0%+F;-'
    'UCk<BwJc<%d)I?ZwxA?br6)W8<8k&e!B@q`_G&xz&oFq34^+`9?z)U*V8mR{R?uxH5!K@LoA!R3$mRl)33bF9!^~;*eUII&Rhs(Z'
    '9-n%=r0T^elW>D|g31ZokJLfBgJqFMAn2=?otd-c5TdgSJ-'
    'I;nNSl*!`;FkE~;G6mWvq$i27VFk)bq*q7|BrvoFVX88@B@co!GbpO74E4w<V3w?rvGw0)Tt^AVr!76$)xHqpoe@4d2*tg)9d2sU'
    '7Hwov{<Erq6bPk8~(wDyU{N*oydFMp*Q*EY=!wJGG`h<TQ9Eft`73w(=@pB|6SogD9^CUhYKINJ-hTkD)P04K-'
    '9raysvDS87&ZtWMyZEvbTM}-?Z|Jl(jvW|n-'
    'eXqc>mB(#cFvPYZnDgi!+*d>|N8&fd+#Qzu4LQyeUulmWB;=&iVv_ODx$v5iTmy`tv*MsmV^v42rq>9P*qTPPvK1!AiQ_NTj7L21'
    '|$&BFMqjm%$j@Et^(BR(>HFMKW1#d_FB1ex*R!1(%-1H1-'
    '1)+Yy9}}&Yi^H_zXK?v$#)=drPk~@Hamf@FP3t0Xj|KN2=dLKMjt8pBs8_(kjw^QhUnWKg;-'
    '0xki0po9;v60VuZ1H49H6E*tR;@27$HHt3y;%bVAvkp7=E$*eKHSFjc1nZ`BnO!{Z^(}uBx`fk{Yz9^n496aimG469O%@>;DN9_B'
    '#9&EvPxaU!uDEWx|MDZ?hNpkEc!$hPhn7AN0eycI7q~qTjwd)&lEA!gpc}|D?P_YxvH_J2i`4azPER#-'
    'RjHmt?{nkEj32tEO7u+u}BgIRIw@8PF|ByZtT*5MbM0}1h24Bg!G8zNRK9=*4#QT%&v}Z>LiffNN=oANvy+J+KoRnsbYWswKV$$T'
    'HMV+Rk&nF+u;{w*)ml$iK26~!v7&nA7f?aSfp_$m4ukToUMcmtupKHuvPrKfv16am{iOZ`7C-;Otk#mPM-qA7*O6S#tmS3_ReNOl'
    'Y_fOvm{H-'
    'pXBpRAg#Kt%$VQzW8zwjg0qvbfFIQSe7?3VwDT;haxY9GV3<r>bJw$K0_L3~geg{tF}$6mpX_+N0iX8a@Onb1~DdVbQ8RE-'
    'Gb?n^r>a@6a}N5Ln#*Nm%hka+|n2wko^=MWl5u2)vBUz61rN%+xVIvvtK2raVm-'
    'mR`y)`2N&A?Wi=KQU=gN!Jq_#+>Tc$93{M;-7=z7pm()f0Qm8v1s079967O^_k1LyQ-zmZ{dOJ_hrmPye)G2oAHlc)tcEWZ)H8ea'
    'x3e><#nwUN7cNS_d{@J`eNv>IVVB7kb_}G&9J23qZb&OcEfVKjcdtuq+VCQDYu<;OY&R>Y2=lUmvd7z4&%?_VB%|`hgzOfRo^X*Q'
    'K}P2Uu3?K?yPK-V@TzOZ-stcgT9y=uX$hik?bWsrLw)=l+U2PT=Kt$dYaAj6U)EXn3b=Er2!u6t)v5(>$~OkVWatfQY$X6*OOzoW'
    '&Dl)EG^qtUFYx75F3iWmFx30(<#>+rq86ws<AI@p0r<S(kRYtrr36_7sb4p#TwJ`==1dJ_`ELtTGkjj&rNu7KA)H4eS^gab9<GwN'
    '#8{ON^_;IJJ(NC-'
    '^%MsMg3g)Tv``|=3K%!%X)615mg>n^Lj05{7~P@H6zQleR93OJPtNg9i)Gx{c=s<yeaoYI)FO=Tn8}6TV+elEqVXX$I&>B?3Z*Co'
    '7H@8#y={@><7~l8%*En574f2`{nwR!a~aRWVJrkxL2N&U#FhRU^(x3t+K&1YBP=BrZLpPG}y{@%!WFj*R@%B{g-'
    '2xd96HYl{Q<){5=|q&2-3gynM}-'
    '>my4uwY*1tl_u6;{x=veHD6OS<GnU%4R!O%<COF>%WIV~j??U#Ue_OGuN?QuIWKwLv!VKQ*_N_jSr4!L|M`7t)|&WSgZ;FJ%<GqF'
    'k0kxh@)%aeKZe362CFlsR_=dg9lKX)sSc*gS>`7VhJoaJsiFKXw`Y0%BKwu=PUn6&l>M67GuPE@rU5uq{iA$7conAH3{M}7f7HzW'
    '&1}?ctveWgRKgcrlZ+TM@hkC>&}5@7l6~gfkM8d7>VgFeoJ%uz?p%K)&OdePROctrcn(jASS+<{h+&h<-__OS-'
    '={tcu~}*W5r+l;5e`Ir7H)<xA=N8Vp1)eebNS5A3)~7khQ@!uf8sfDVg8$3cw*)JhM2Xj?RAZg`+%>I3lCp~b0BVK=OE0WO?_2!t'
    '3CJg<hz_ZjpM1o^#FI<vu6*_E9i^CeZmHI?a6KtqxSO$pW`{$7aT8aM}zwXenNbkxOQH9N;&Mr>bZwehY2hu-'
    '9uV_ZfZJzcs+KU#O(pQ!DcjK!JMOPnKi!;*iRgtz_D5s?^fP$u7$0=gzT4d&3NqX?e+U($Ew)9rT$j?haZ0EJTCA^d<y@<KG+F6;'
    '2&s+aV_S%ZS;HFZ@E7cyB1~`|L69I+<yOG)pX*2!Gv=Dmih*ti6<q!J<b(7a_?1_N&0?qJpT;8qv5NZFXt4oPd^vFPlIa^T7;gv5'
    '_Pvz{y@&*g1-PCEU$CLJ*R#d{mSkg^|xF<kvd%TRqVz6<o<>KRN}lG8v#FJpOtAeIk&-'
    '@<7LW|LnD#Bah`7|E)w>`Uf^#!x3H_nA)+rOo*d&#*-yb2_+8Ec<9J-'
    'J#wY9?eJ|Cv!oQUJUY<+KIHrBq`ww^?{Uxr6zSsWVd+)V_!O{2dd+dpgI5+;AF~r6r?=RR<_!1h9)SfBjg*z7x?u@t`foJ$Rk_RU'
    'I2wYP5k)2=SaA7CaR*!hTpEJBRY^xe+s)-'
    'gnF0VtxJqx~##(4j}@J{0I>{aQXd0t*#4>b0!>E1=&n)3tENes@Gk7vBc9KiS{4M1U(*o{VC#P+I37nq#m&*%yfv(IaBMGYj+k!F'
    'nHoUuh-S1iYelz*=4&TW_TX{4hld`TQ8<;Z5(1@D#lUTu+2?BB`q<QjBVa{iWbb>sI9<2%?Ja~5-'
    '>ax!R|yTF)e!i<BDtGO`e?0S6EuEXbfVoW6*&Us(-'
    '#~e!sOOj2pT4kC~l6}N`3ynq9WKa2G(jZem%k~8+hnT&$)}V@2gLx<ym{^YT;uSCA|FC`d9?j=d?8A5pPRZDyF@kxFd=+d4{>F9U'
    '6C8`N)&AFOn4#lAKjE18IQO51pGUnkuh~@Y)9~SxL(cb=v#-aT+oe2y&R_n=-'
    'YL)X#BadqIX8Sw9GWt&ndgTQe^p#Ni*Y;GgkvdRTR3uw3+(!-;Pza<?oHq!sh&LN%6W1>u$TB;G;(yYBhNKHX#5Huuh-Dxzv&y`6'
    '-_uZt_28YC~g?n&F>Yrj(qmk;8(XPW{v;l^#S=z95DF2d=EPl0|~7zUpEWKlFfu4$@f%8D(6u((MV{MUTDto$ayp2=iabUvz)e=*'
    'Ar(!n7-nF+?$+3BmPlod>mj;ae{I#5!VKOEbO9Lo_JZGoERa$!Pmsu%5c91{W{q#uS?b}zb)s#N%ykM-'
    '^%kSWzS~yflG1F#1qB;@mK7JkJAU~d(u7)jNSc`>&y9QgJD0v2Qw-'
    '+#yQp9(!MUwpUnFC0Q;4FF&|e4<8kGAt<CNM?}_WC9DU_a!-'
    'ZvRqfcqBRgP7bi{bqYd=}p+)dNi2$YvZQac6>W<B!6M@|JTO0&h#_nA_`BZLs{)a?Y-'
    '7BP_D~`*J^zI$mw!k7~W4oS)ooxn5b!k!{K=iTzU2R1E%L(pk&xNuxhww{k48S<F)!i9^-'
    'Hc~kq9^LoXF6Rx9LrbB4T$j`(%O?J~dD{@29yr1X%YhAB7K=+dGh#MF2Nw<Y+&f|09ALX?S%Y21b)T2%|7)rxwDE<fjlJl%$U)-'
    'kJojHe_7IRs{_!zd!=SFX`ono|Fhvl)dd{4wNa^KJU19=T)O}D5qnEGdqy}c%W)YOOG#C~~RnAZH|96b38Hqcrt=K?cV(DF5FDbA'
    'C$9P)cD{UdSXc+GM0b(-'
    'pRasAk7s9f=8{G*}pqd$WGrtwI&DmVG2@Hf^m;_)jU5q!9GKNYu7Zk2pU7?Ai|`Pww&$TgkovV8pf^QKx(&G4i_xIV3KYQwVrpX?'
    'O&8-QPGj4E^ZbGyVG_NL=;gT{qySLSbPKd-#Up)i%f>b1P84-'
    'c_E9#Wevw_mQ$P^w=xU|o|RFSkb%oT91S^7nPl`M$l(3CjL=08UVj-<SQb8J?2!w#sX<SGBSYnJ1JxnQNmrTTkcf=pp>A-'
    'YjRZ2`15+oqxjAH5Z6~RkG=zT%>0Ik>i);no2runRisyCK!Z2)WCl$)u(LAN6N;qhVf|-'
    '|7zfsHftJ_n$>X|qR$QZufgghmHTrO{4Lq<Rl0wJy-zKPBS%>0q8)|i6#S2!ExUIYZU27szP_%^m@(7!o#4yNo;{m*YIVw#>FuLO'
    'k7@t%%hC4!M0@>Z``ED~y^S9~%G-'
    'nqqpNe~Ot<gPtSneCyVBV?x6;u8<}@STpIYha>h##FFrorWTH|r}rAxt%h_j<xw!F4s1F^@I{(R-irIqE&(Ut0~*zv2gW=-'
    '|~C^!A*{Q0wV9@UvMiFZ!7_vhA@En8IEv}t{9>(-4eeSO=p0rs$U*dg;BVu-}VSf4RBFwT+Fez0ZRwvC*Jzdm(}JwKY)M_LXa-'
    'q&*Az+SgsUmu*4UdJhj>)Rfd7_{R@#PYGFor^tA^T)5g8dse-actFWSN-zKG1bwdKdp`&Il|wYJb6NO`t(U$Lv`A;uc|X<OsXzeF'
    'uk&5$zs*6@kUITSTov#g;pTA$s)hbwQIrM7N@pq)v}5`R#vWDQnAk~ixw@wmX*14XS#jty!<uiN5jT;@9cgpv}@Yr*GV&**?+BVp'
    '?&>zFSfIF9eecy*u`z9cJACMn;*_upS)<cz1q^-3vO4mojW&K+hR5&HcG9fP1bg`96Wfq<=C;~Er$*ruB=@P2Di-'
    'YxYq9dQnTYsw~5_fzu#QLk|khqo#roVIKNs~*F5vz&#Pa2@rgfT-zifj*fmbG-@s$)^4MeGOX8B%)~^R^TJ8Q}*H-'
    'K4Sz(W>ylvXF&fo9pS!3T@6+XGde6rhZiG4S3USG58vd`C4mMvZ6=f(S6<Gy`;_8E9dk6-KN%^Tcyr%oO7{>Z&rxNyGNVzb-'
    'r!Uf{A$HR_iY)wnt`mEdC{>P7D-'
    '?hh0{+xb%;DBq!fqB?HTjD&Vj*j_uALmx)&!1=hG|Spo^p7|<^d;9}_qMB7FV(fL`t{c*+)KMRTWjI><~vKxzAMb9dWiiy9+6{3('
    'oNjAuh;uRZ!g&9b~^?*#}0dMmyIvrOIyuOJ=U-B-'
    '{s+x*lJ;I`LbnpeCj%_sI6JMys~KF0>8)j=j_?jc{Ka4;yC!6k70J*?svR*`t%96)ul@pyj{LbyXcP>FA|$O=RStL?AqKH_wL>0{'
    '%m6b4PS5n_~UomhYx?-{O4oqm!qnaCXKZ|_@(vP$v(a;UfkvO;GUU3aGbVFm(Dkf9pUqSe)NyCXHVGJa-'
    ';3?W!Ee7HB?}9Ers?KF^7|OU57&7@1R{L^^VSXqfhMJd%$%h*RS8`7|e<ltIQAA+2cC1pZVnKuG-'
    '4A=0|&aTK4STRomDDCcnnU1Mv8@oU{AQo;|x-%%6SSvvc%5diO5#<n4?beZ%a?e*L=koA`r|n~VcTj~-|-'
    '|22Q>p>I_g{~5n*PVoL|{>**#W;XM&TYY8qYH)q{aqC;?6E+5Lf9lVk3H$JvbN%VlUu^!OW)d}!7^{yqXss!(CA=eaDw8&189M@7'
    '5)V`Ob%9mxE9`xIf7^j$y=_NN^tBvvtPbpLtDWn58!s47yE*q3J9j&uKD(dj+}-eb<JvXWzd0xWa)S<z-'
    'D?|Pr~B{s?%io~$Je#(+k0$2ozOmF#Cz3o<36`>{ww#fRjZcR{asbtu>)PvVjjfbtk2MQYcv~wc)x{l&wSd)Uh{SOui5Tp*pT+J{'
    '`m3F*w^|AyoLj9d-i;7=f6MWv>nQ8lr`nQ$$o*iH)wz!J$lUk|9IQ^3rE{dpFh-'
    'g;uLu1!L|cmqd8k}nzwC(n+RUGlX=waa^CHS|6RLw$>-lom-_3w3$xRH&F;0$kt1z9A8T{u1aFfjO|&tMbqaI+JoC9un-'
    'jXMACqUnShB`!w$kp~GFx9PiFvT-yBjvFX3qAp!~D68wSe7kv(Ii@v)&l?+iy>^zU-VXTPr`b`*<PYMEm#ev&TOBJy`kS#CcFmEa'
    '%3RoAq_ygVM)t-n4!A?Yr(v*KZIXGkaXVY@eU<*qDtQW+ym8>^*P9`klS`J&z|oc|yGZCtH*DbJV2YsXAfkcTSx;-'
    'R8n+6`DP_xuDA$m>c;8tP@t+BizA7weD_szN@XT>^46E$AhZ?x3|aVAoG8Ff4?`@mBly*2WwyJi4&{?s5Nu5{^O62hP`;9xZUHxG'
    '@sd6bFcN(sk3f>es|!&?zX<Z-5&3kUZrA1$Bud2Bhy2IZ-VCAJ+~YFa_VG(!JIvFAz^SgZ{ALIbno6J9*qXi{rWGz5KDaO?Qef0{'
    '{4&hlb?TnoOApV=PsIZLOd^}r)Q(jedHf8rm+5sb%p1JfYEbr3yc*Fy@&NjkG^Yt@F4E<bz)H$+E{1CdeUrsBCSDV?TLNt`3bk><'
    'HxEIcf#6q<to^5AKH0eYdv%3tl8{H@bC^Lj+o6Itw)c-fjiN9{=(_j>sQV*u6nz8kvd%Pbf~p-'
    '%yEHRw{E6A&8=JCrv2ehKRq&={TeoVnzi4|ra#;F?j@ZG;XD~<prxm0likPDe&6ohyYKD(ePT<u-'
    'REs?wElnHU+eQbckV_*zw=fd`_T`~zs$ymeGSDL)cnuao2;EKT_Wy$(m$iwTxIsy>%Lj&DuQ3<bM<c-'
    'Muv{>OPcvD_|J>_uTQzYU+cg8`a}KEle_irAKtEi_x-K<-TRm7H}0IT-'
    '@bF9e&^nGJ1+Za@Vj4!J$?GyuxHPR`{x+c^ROLQrtlQ=i-+jR!lfRNd)yG)z%TCHx#{i7m5XNEOWtnWAg+gI)2-'
    'I;zC(KodtG;*xOww>)~@+@%UH`8Ogn#`I1aJaZ-'
    'NVWE_6+qHyQI8*BJk?BbuG`^CR?K`)}^mE&IP8Y~B%$^kZD(&tccR$!~ts+%yR8rupl+fA_a%zZUv-KRu{F`T<}3&fB-'
    '&65nS3ezkt*?v+>aXRsObG<M{1V7o-0u-_7Yll|1Ldf(J@<}SX&y|A&^?0(1BPZuv<wy|rU%_m<+4bej>PepUt@#AQ3p7XwH-'
    ')%i|1m4Mcd||+~4{VOb)gRh;a_c5Mwk!3kSIiG@T=Ox)`bNE&BX0O>^9%dVrMg{v{pP(3_3O93sb9N#D`F6|Z_R(N*Kgm23wdiu`'
    '{8TYh-=4&H2f*I6Mks+OXtx4{JMV^n-#Xb={9E_fDh82BUjCAw%=Q>+nn<ziuF_)mqT}g*v4LtmFC9#_iqOm`i}VvbLIEeFTv-'
    '2bz8o8@ziV%7Q$HfZJqHYZ`Plp-Sl?X`Z%pIH~3a&zoGRMv0XF!(QohFgD*`Vw*R;bx8-'
    'JL!~TY^@qKK^Z?PNm1aqkT?#PkDNlW+S$rHYg2u#jx=<{UYETPrlzPNusb!nLg4%p`>eJo{+uyNK~F;+0Xe&hCh`t-'
    '5&`=5PI#pdN!*z{Ysq5I~YYu+0DEbMpZ+H2Uauv;;AU2}irk$!#g;x~4#(oeqKkmJ-'
    'J8@}wezkK<;+l+aGMhu8+XOFRee;;$PT|YKEW%I}}Yve(qRe7eBmSHR<9st~HbT1s6v+E|F{2=9;u?Bef@KK5Z-'
    'nv!Hv8+>?<8Y0B*32LB_Nw|v>_fS3))~x|w)XHi*O@cq;}OF->f<{5J^EY0Cp@3Uqzm80-'
    'gXQ>mKy6n=34xP<8nWkXV`!9NDQc)V^)gQT0i|RaF4sbW>cO)Io7PWZO)4*$7h?@kkWY6ti9TPg})s3wHnu~^+nOhw?oVHOyY9&W'
    '9c{J8n3EPq&b{<w|G47HZ$LJTbZw#@7y*!kaI^|_=fK(StpgX2K#Fp@;&Cq@4Yd;TVH6X0|PF|>zwaVv_>qXnSLi@cxJOSmaDx25'
    'ApRHwqw0}@}&C;z8H<QHsi~AzfSzUh=r45cHQ^Z#3^jdOLLp%I>sN?g*FHJI_K6c-oI(@-'
    'Dk}AHI{v+HRJsc(CserKJj(z%6+@;>tJhk%o~0Vwoj|midg<_pF4T9^{LxFui?{-'
    'Lvs7}EkCbloM%HT;~}NIAh%oeG4I307}Xym#CM9mb}8nX%kg;LTdZIF{uTDS>0@&--+k+Qr0>4_-'
    'u*SJ0hIDY${0&o&%2n{`WxeP;TzbK7%=vrZ(@t9@!veZ=PlD=XuyI?Ymp4=$nABrX|7&&p2>F1ZH#}|44<M8V!I-'
    'SbIJQ7<5n@plJkANVVuS9igq)t5sLY)$U)38-'
    '5d+$JcMgWTfJXT^JZF~W4mIk&Ho#JyyNz}ckhn>AL|w#8837D<#x>M*F^s>$DbQ@)^*Mq9@(JjK>UZe4x9+MDCCdB{rLFfkK2b29'
    '}bVfc_1T3jA$P@a-{P@&}1Wjdh+DSUZ)100}YM{HCSk>DI&eQ;2%*3NIBQ4-QxTj@`cGwS1le|R-@kY{6ja&^R&r%=l`j-l-'
    'D`R>K>*4<M^s?Vvpjbcx@g26AdBW>+bIMdOqYSD(Bqn<eUSphie=+Zd@K?OPm#A2)rh?24)0SG<x)CKSwxO%G2jPY&K=e6mR3lk9'
    'V8Gv$59x!3Q5yY1oqgjG9yF8n|}&B*9&(MGYl!6~xU-t(pDAGg7X*_$fS+2T$Yw$cq>6DZiJzZ{PK}E7wgN7Mrjp#Xps266-'
    '1FRFKn7%-jCIq27JeoK-z1Z*at<1&FSlI9%o<ZbNKB!>%-'
    'J9DE4prPw~rYjW|v`Jz9<<C0HCeIVJ+Z3bV6*pF<*XX3?4y9|5kGi(`rALj`~bFK<`@L-0)J9B#yQ-'
    'VJLPlRiYKId_3;ylU;Vhyjnr_cmXn!!>3#E(I&N|=ps8^ywDaHZ^+{Fn30I2Z1_xO%$hp-IT~QG=zP)j)FJ=bHI#=uh%ne-'
    '9oIHUYZ?d*fW9UYDN_oFdiF!nRRAEAa<qPyA6lJe>=6S6whY>Oa6pu_Lxq?3(>1KE!wJJX`D-'
    '9%qzxU9Rgu{7TxL*o)(+@md^3yAB@@br0b*U^n_h-'
    'v5F}={0_cNtJWLt$`1<MC~c({owQPu*8E?{ivu3=C!+c4nD_qgKr9}(|KawT*DJP;)?}d*x~%UsCkw8xyC=vm$<k1W8z>)tEO4rV'
    'wUfz`aDU0l1KcJ`;P7GT-'
    'x7%|NSZ)ICLnPFVMM@?XYEV@e+3r+nApcW2s9EC#&h<d)tEBu_x6w5@saMLcHf=i24U(c@cX~@q6diFyG;u@<)7!evSXB=9T!R>i'
    '?=y$NiB0B-|-DaLfnvRpqGUdrH|b_UOr%@n6ox&X0TpAD@`d;91%{;r5C;W(|#V6Sqqo-l(nS{0s7K%lxCzuyZcg-'
    'o5+071+@cVQwjZnx;A!;&0`AFV0yt-Du)+>Y752)SKo=`V)5KUN2w1!fdymX143~erfBWSkLrx6mtDK*$@68`hMI4#yI*B^R10dK'
    '6f&|G8f=yaj%>c%($#^MfWk*7d{q*j;h;1I+N`EOZs(napEpqxY)L554aK78?k!ujy-'
    '0de*5M1%Y<Lj0(Wcpj&g@p11+~Vb}YvB9d7S!+cvlL_U^FH$#=PA>qGXJu2}{~=o<dYlO?a2u`uHhdYwV^C&>-MR@AD*?-'
    '=7_E$01`{vZx`t`#f|PyAowXxwkVCLW{TxfT)YefIw^UpC@!KmGJK`|NM6Cr(_C_0(>A+-o-'
    '7>lhOFoG{>GTs)rmI(c5dVqv+STvj(w-?#U#1t;n<_)UgWE1plx`-R!@Nm{?CzDJfb32)HtMt{YI*e!H*ou4f&;HU-'
    'X8nLPY7o0U8KVm*eb2!(FZ!iW2_T~P-@8D+=%OO_Y*th?ms3rBc`lClb_&$w11F+yC_IeaNh)2a?lm1VUXM8^4-'
    'OQ7@79sso`EKMFK6ye-rDtKc-'
    '@<NB10(n~;YX@V7WG|Hy~3D_(;7<p!_v!!lZ>xnH`e0j>ppJtJH`X@py5S7dh{sqmtud@CZ4DA(Z!dIHGJCd5L-'
    'Qbc%S*kMe8@e*<6#)*WYEexmW|yUeupIe`(iDtrV`0Iz~?%AEKGB#CwnH4<4Z9_eea4W;MSuoT|VqpFjV#p75hb<RM;9xtlr1D%0'
    '6;9azRE<>JD(!sf(gus3}^a>N^Wa5>*d?~ALPHEI2(^?A-WFV-&jFnVq90jVQM-Z{GYKRMo3T;rWVaF4t_&+wxmIbL2X4bB_*-'
    '48#&S0WZfoa4Ulo7q!GEN4J|Xep=Cd6lX)rhYDd0)C}jd(|Z?#}Kve7WargB|Jl%81_A}&P#qN3}5*W#du#}z2tK2+SLcX>#=|WY'
    'j1`hJxhI#m_6}TVhzMO&YwT+v3+8T<ytU#9aZ}LrAwE~T08@Cx^uornSYem-zw*dH_O{C*L%q0I^vVb?)KdKue4~DCnWo29B8fm{'
    'k>zyj)QADK2DtFhaVn#{FL|#*wJ_26?p@{{`$Bs>?rJO{q;xlf%E>`vuFG3H8sn}9U>3;wc23y-'
    '}3*<{cR`?96n0_S1qaF&G<Z%^LW*F<#)25xa7fA_8cHEcE(8X6XKKj6nFryPn|mE`HaN4uV267aX;d-'
    'j9<jVi@4hDA^qv^v0Yw2tXy+Y+`+6qOzPw19CY<>@Bq~;Q_hOkZ^A6aO_xo@JIOg>!r$;m<``So`d)?kx1S$(&ikHx|MclIjxpJ~'
    'q@mtN87C>*tr<UcD868szfktKoKq#uckyRRHKWqnT>NQqzrX%^Z>p!DH6XT(`o3C!rnx1@E%SY*G{iNQVmBMx(|nlo3B=)HZAr^*'
    'SjIqxvfrEXkF@s`PfNAiq%**LAnb_mXsyMyNRKntsNUZWA3D-'
    '@(B{)a2ahyx!=!T|jR4J4`B=_lnJ*#D?p#Z)G{&deQaQgj=PhLXg#kYHs`^H+!jH6`S6-O<R?gRzR=RvZ{-'
    ';N+XTW&CYcB@wcJb1MhWe+W)19sp-GrfZGKS)ulxsbe>(!KbG=uR-UbjxvVEB<@8M2k~Q8GSZ;$89^%?~+_(m#*gXeGbm!NY6TuD'
    '0I){;FdLrTH$Mzv{o{b#q@;PpEuNrG7YoLzCCB%J8GsW_5d-'
    '9sgDM(IC9=2Hvjn0&<^FOro%#{NTFV@b=wno;&vaqnq^y_Z~K^o0`=Y&;7Z)&X+&t^I8+GbA!Fg^G3NJm+d#0ol00yGyKToYl>Yc'
    'ZcjYT_PnkUHfq!;$Bn>@#*G`7+SsvU(<Ar>I0*53enX6Y;>3yV#BZp5L>!a&I=m(6-0_`pW5-'
    'q}PWrq$Ywozp{En%W*&Sb27IaUkEL+)8TfJ^kZPl6uwdG5eHPopmj?1y4X1o6<+CSsRkM~FLl>#G}Waspi{ofq>&fMyhDRZpNwEu'
    '>4G2hOq(|*4&v~Ri+zM^<`;7A^$QH<X9Y94nbcFzCXf2Z0Sin*bG2iC!NIX2kF=bwL03>93+?Z|7hjW_B0g@#f4m@#A8Kl|)6|1Q'
    '6I_uY3r4hCKo*oWJYHe&|199R8n@)y<VGrp|MUofq*bXjL@+x88$-'
    'oDMXb?d=3RwQm0*B7`)gGL>A7WkSlDYZhguG4KbZ(dh=T(E%H$l}VPMN7>VvnsP@%}jNZup1Z_`&!lz%zN}x8oUbP0>oB`huSrjH'
    'KyFoG+u*w*!bw@Dx8Doc3&I|6mE$>fxlrpYW@&!rKSyd2KW)z3(f^@B-'
    '=$zAow_yuFj51_o9W)<yyJYY_?=cZ5dd=O4oFg9$kugD)tC2rFvk(;E1<L8*bUMZu6}*_Sw?P%9ZQwIU0*AymfZ2u<v94E@=oU#_'
    'I78#t_DO<~YWm7*o*YBQD?=9NJUb1H`=Ranz_+mT)BOiC?142L8!8(sx38vLX#i=_7)<*j!rAV)kB>3S1&$+I~NZ+-'
    'mwI_#~V`u(yr1O`Eou?ZIWXrutgo7s8KZLt${jGU?Y~G&F3wcro#DYzA*&qkW%vGaS3Ec1_^3XiXM)BU}dIZ@GRVYgg$&X^oZDJW'
    'W`Pa9?buCQU|g2<!)jM!%NsALktP)!e4|KG%YNA{uth@FVa6V&23O$yeXC>udY3{q`K2ZL|N|Z|8o*?6x27o!M%g`Q3WApPH~Z8a'
    'QX@PbTb0eY>z>m-'
    'BtFt@)$ftCh8#JHdMUgp=y}eH{|}P0yWY{3F&Wot2#H8*4eov!q`so6+!Pd=!i?e9kfO7(4wrzQ$|%i}e4ZZ#jNs{#uT^5iiBIe&'
    '1HFCbwXH%Z3eGTCiPjFXQwf8?*5RFf953kNx*kIIZ*^<)8Ruj;~`s{7`tCG&@zlFLdVIeq5{c85RE*h9upvavig1iTfnG2{-3`Y-'
    'e_9f9IWdyq+1_os4<pTrhre4vahWLt)?egzDp=rD*-Y>u{HS@yV0N#FlKIceHKKo}-'
    'R^nBSSrkJ$env}<B5;IS?rPeMa6@slD3;o}Wsx-=!Zf0}2451X3&6~B{)Au(fKNBuCz35Z(@C(q(@&Gab2cHLIOkLX`^KYczxM-k'
    'pMHO@i@(EAGKn2kAp9-K3CR&a%rW+s>*I#;aGn(3~g1$g!9mB5<7j0(-'
    'aojZ$hmwU;va{MjFkT`E_oBOBg0AlZmmnBVA>3QO_TnBRp7%=g5a0S+o=wlIIB^FJLU0RB{&QH`+U_5tQ;J@}iu6@dU3f{}wjXsL'
    'sOJlO&<*rZnnWh{H?58{uU9;j=)FEOVCfAW1(taC0tr!0IqvxcZK204nxJSKao878IDLuMWQ%Z5{yv|5jFG~A?BEP?=g~mCl#qZc'
    '7=$r<O+2E|wVTl}sghx>SjkTF-TGH@4=FzBY>2rl@TdHY{QSCwA;~uJ}B|aGXYKf=7`STt;CbTKx?2r%n<jGIj`96zz<~Mu4;2)h'
    'nea87A*iUQK%=g?5!uldc)==x7aZ2NU)X;N3V$VS=0v{`Dx`oc0<0jIw4DBW9H6{H?<tQ<hDR(TdwW+)=>HlIU?i;^nJ;YpquVI%'
    'Q^Hv{IzJT;$qpqc6lC*vMdOhzDF2VEX&k}}s>XbMy;1w^uPk~$Th&G`57dWkS*WkmbzEpwVK2F+!e4pPBrEAA=;gLw&PWwc~@T7C'
    '5cqRJJ!GDu}Z%f2rJQpFxRma7(4pOW@_?wzy3h31d=aUAmaHE{J%VUx6btqxqaMdnebp1fP{zrDb&;D+$zriph{7d%AYdlNCO);|'
    'a-o3p4MeCK=l<<lSx5(FtDaM@RZ!~=tT9(Pz6bH*Oq8xt<9JQeZ_ef(J`fI-5Z!+%;&{V`P@ip!*{-'
    'Ri=YQ`!5qFfU+*285jo<ZZ#&EgJ<N0ehmWeg5`<*|x9hRu0|jT&<G^VqcfPjjf^`Pf(SdiC+h{ZKvGyv|}nL+2F@yBNdVub9(02i'
    '4u<QMLGZ%xlI(jJ7V#uHS<n<#D6I@Q_?Ht(m5baA0Z53LoY_r1`9RznTLSr<Dd=6CJappDW){9;0lan5%3YT#p7kFu&L3YsmfS_u'
    '8+Sz7_u=f6FwRnqrv3mav=hY!pM3CSbm1%j>L)J6`a{`}6BmBUrgXXeny{iT&i~vS(gHC&w!@jiOe?p8rVvsH_jxO#f7USlXuL<H'
    '*m5XX8s{-Da&X@|wq54=a9~<1ew+a37Qobl@~;F4X!&n2GpGtVzl-'
    ')F%9+KMFs}_rhtf7w6Zev7*dN%dz(2y{oQaaOe<wutNL6_F=)f+?Vpo)JIkCSM!V3*ut1H3^T<&grTS&LJ9wNUgq7qcbe)>mTOCv'
    'b>99S{7BcA=lamN_sSCxzF5@4F6zei&o!4k=jqZV_;IJ4BYo=B$<%TUMrm*hQx?W9twGfz%=t5XS7U?p==ycY?l`Y8Yr)@DyPNmj'
    '0Y3Md8h=CLM`b;WeBB{m3EL)pSM})|H@<al3wcWS?|<uhGjNsq+r@^lpZ|~gJwDfPj2!RH>qPfsD>s_qMA5*YZa1_7AHM5(K;*|Y'
    'vtN#1y^dzxQ23E-m)oq|v=8EUnp4n3DC+Q@NxX9!c@qVfP~84+2WaQ%+_f*tTe;qb#t6RKs86YJ`c`JQ{#Mv;U>-'
    'uePV3@V*{zHrmDkV2?6c-'
    'M+r)#wkBH6xGw`G3;74o0kLJG?e#C!s4&X<^2a3jCes*=*w4zO(Jj1c1S+m{@KO$~37=EPuci~47>mg3&@mugC@Sy)*{Ahix?=|r'
    'wVnf`Qz>iW*tA6fQM>OhPEeQN*q3!b*J1#P3&MWaFxGcWcw{hHki?}Q}gk5{u3*@-'
    'RKNUY(vAnhfE|>Fg*1i^g6nrT64VrMIqTbhXw-asAqGkTr(LrBWXtwKe{Ak6Bq46W>w1XWn=83~a%wKqU=yrJ=Rh)qT7W`;MBYw1'
    'TBbtBkVTcuP3XaU+_z?{|;)~*L_2Wl0?l*DD4X%|};78jU@S{VAhQ^N~Cq30LQ~b-u(Zu`tXW>UXcfwgL@S}C>w%WPuv+Fr-'
    '*LTqTZM*y6Q20?+zby4@#z)Rib~L|kf*<w%F8nC3$qWARD*On)fq!Rx!ug?pJbtvHW&QfiEd};Q&f8JPj=++5+_!H}!imJ!%JC!k'
    'D8%B0D-'
    'e$pc0~Wp>xHQv9AgLPZIAyj{3!4m?2_gIxV);9^!MUNj~_qwxXk|jC)@h^4mf^v`0yFWkHC)h?j_%s9N&|^HV~&o_))|U{T?^Nk2'
    'Ke4?h&U`cqi{E_W6&(kHC&-'
    'HcwQdPTn7mAN}~_Pabm>r@_V|=alsJ?rMt~grVcvk00f^z>HPcHm^acxgg88_UjYY^v}ePgth*0_|dQR!XJO|_4e7baIL@r(8$}H'
    ';t%3!@ml$Ig|5*)<(xEdyo4XA2Gjq2_|Ykk**$ska}$2Xb2I{dKU2n!<bN8YR0}B9u0!HSimCqJj~^wy)c?VcULQa58c5vhJ9pq9'
    'z(0EaKlsrb;zz^`i6Nq4ckI~l|G|$+_)%WpQnBY;*Ou4HDS($(#*gGDs@p@q%<!X>6CxY3hU1aGBkq8(6UN~G)9@qJ@+sp-'
    ';sGm%Ky#$#7Wt#_xWG<QOjW)k9S7lQW&9{|oCnmU7%VpWe>#3taM_L}yt0fRWj>g4EMmS(bwpzvZNQJT#(fR^Xh7|jzXv}mw?7g;'
    'V(uvPIrsS-Tj)9OPca@fKG$5WwH*BlAB$MN+n&$L_>u5TY$u-'
    'QQ25axb+~>vepGIMG=6m8069>{T*siui8_+FaKeu?7K(48IY;$_hQg1^<L*BiKN<`N5r6BC#*fhH1VcijvuGz11|Y7n{FwWMCV}u'
    'H`Bsjtmhq#!rcq&sq41+S1MrV#oSE0fkDAqA{YT<Q=*#6}f7CWs?nT0n^4j8mBz}bcS~L3zL&`C@H>o3)tpWcV@T1!e=a}P2|6u&'
    '6wF!RITIRsL4t~_E$$t4>I-ZAy5;2TDwH-'
    'V5)OvcT8NaQva^*TWJnf%+@`bgr?ITByX&*iMbH{EJQ&von_*=whs7p^g+BMZSY}nwjVsMqIQzuuaO#7lbWA^CEocWU~^E;<jX3d'
    '>YTe@O?ZPl8EwPh=2)fRSj)s`$Q>O0WLr>Bkv^?ByZnc}rbXj7()@!BMlCy%L4oH*LsS6_{GYyq4>nk<U<O0TQCd%5l7iH&Treds'
    '>hhxXOht=r`9En2j!W%cR}k;lHTWy_Www)bCGnLD?`@so~@?v!7WtrI++*4f!n89#np^{;>Zu>D{E^{w`I-'
    'Wgu~=%dftM~oO*9Xobn`)8kxuZ|u)!E>YwY-oyer#N3Up3n>Y&;R_-'
    's<jGn96m#9hCFoaJ$dqU``yIqmlMCJPMJEUGH32rmDzJ9SGpI^Z`rZ4r=@TAmfD)NOTD(ks#VM4ajDlCq2>eiZm1PBb0(YsVv*oc'
    'lkEP@@Y)ePQYWh57tIp(;*HoP@6VZoh8cQhowcs6#U9&VzT9i8w5(mb5&lG*+0AQ|kkf9qtj(Uiz>dLvfSWZh#obCZ$BBngpTh3d'
    'lIo|Qj%k1Et-rRv|Ne;ThaY}k9W`o#wMp&vzS$zhRGouHjy|z3vsGongfG2r!=got?Osf%Oqw*g^3_)p&6ZOuGiFb7ADTOpYnfZ='
    'm<Jx&X};E7>+I<C*u|O^_{D1KC`J9Fwf>yiBiM26S}>30<_pX0db-'
    '>%=FjgmzgXtHt*)*W4ZH=#p9`HkTBq4yf!TL~b8Dzsvv~2!7VBr`Lwm8C&1)CE?u<2?M=#)qW|!4w#}2!`sfi~o4xHjaye`%nr)n'
    '!#Zg30`9uNMzWXTHq&rbIt;$6aY@jL8h_m`MN>v!KhP`ty&*kfo+)rg%>nKISx;jG${#mj2lix=7XEO#E#%9X^5(I5k7+t9LMLr)'
    '9!F{rDyb?c@U>KtLi_3Oc!`0fhx6}TQNYH-=$w5cszh{oSe@Dq>w5~n0KPK-QazcuPLfi10F>wVO7b`Bp#&-'
    '9#+tKWbB$j0*Td_2`SOS^dS3g2<fsmA&vCls$tSW*$6M#pYn%i+TZ?cCS;y=45r78>usGb3&&+`09qAAcNB{|L=8^OxGvCF@%@_P'
    '{;b*Yfqg!z~*(?zG?Z`RjuRkHbl70Z#%8*sx)9(g%wequUr;<UB5HLac4^;_h1DNAbG95pM$X0TZxwmg8^x_U&!iw5f+0WKrklU|'
    'U}wnhU*cJ9cbKb)A)?!<vox>)UT{CjCF@*b&Fd@epFWhYuf8{M&H^<^>vagm7xb_qhhNu!s}(^lWUsd++W58&da`V=uGsTL1Ggn('
    '=1q)}3%@>^#6t`}|Ru5$A>NI9HnNNt5;;ab4^~T$d)@DK%o6oF6e>#nF3u)=8(4KH~cZc$WO1-'
    'IF%^|D*w!YuX5ZE7uJRoju3Wu^DqF_$oF+D@(W=@m4kFG2w5@e}G5X(b>_`F@Kr;@8x0rdSSvce=*x$Zrj~Qtu^eh)6Tiqu4|V+-'
    '@YB~u>HOUr{;xl5NT`0-'
    'Z1qMY?xz4p#kgqe>BdKX7ev&NG)Q<9xvCi;ZrJS(dLB)?ZhV75iMya%HKk})$NE*o}B}8sq4U^Un;#ZY)D^~?qq0V`tk6I!e4q?x'
    ')-f!>)Ei=)^Rrmi-*>!*K+RMdDjIydKCSW!*-mVb}jw$TDCq&`@YDpbel?>QWye_e!y$qS3jc(gQJ1F@m(-'
    'i{0*EYbS}JJdcFoM^WyP8{x|S9#Yi0QWnD6I<VfdkfmecgbAS2oT)&b2ARd`&FLED<%d(d{apH`R$<|s=okE}GX8ngpkB9xu{PCA'
    'x8ZnOt559BlC4PqnAmb2^@(INs^0*i42VrW`Zk6_1zBW_iyY#ujrdz<N9cQ)sPCU$Gj9}J^Cld1~KCK*%9DhSUkvtU}Gu&_JtK?^'
    '}7GbRhp2WDuxFL;6<}lVa!r+9xVbeGl?3ZzZ7<(_d9a&4Urn0q^-'
    'MeeHhkZEg`Saff_#?4obltf3@RY!hiaJvJQtU>4$$x>pprwkPwRTXheZ))Mx3M+jTyJlm>+zs1h`*T~h{ZOIZ(~2=wCqv5CRP72;'
    'a52RM!y7uldrKx2X|vX!JMG64O=m{;_Di#!B6o$%^BdR-21{uj@h+<lN~qzJMM9r-'
    'MbIi`S0^){j=4^Ht#DB9y}Nnt9bT|I#|?2c~bx3ho9?r?-tljk-wT^Uim&dX|osmH}p5qjzL2UoavYP)2A=c#TyDs@|rgIqhcl44'
    'UC4^W7I7X57xP`=+QD~(KPnva~QV6*YN@7aq?G*)zBxn|Ed|7$NJC#E8<nh{CN>SJrG#!VXyZFR|Y>oZ<aBK`;D&Rix)35O~~(qA'
    'NN`sbwjilnZ98EG0+x;OM+e?{gwDm)C+GFrb66FG4aTQQSLy>p}}uLzt_h`e2QF_(1MjNRz31?J&r;?uJE_OWEwPh3SaCWvjUUzx'
    '>C6wmUuJZ9{cv~N8`%tixt=TOW5z%s2Qg=5Q79q!UnV_Pky8(jo0^i`4WxBU(APpbZygz55G&AM#ROim-%!Z|1H-'
    'e=d)bzD&n8+H;fg+*YfyWj(e1AIrrC6yHyv~f!%X_TVqhPWYbu$=btrvN47-2?&{TVJT?l>PHnrFFP}ww>h1aS7mQK%ydR@8-'
    '}M+7`-Te_&UlOn?Kbq<c&>(a8`_s>juo-'
    'P+oc*8w_jO*i+NbOYO1rRxKS1>OZFm0PAkWF_`bA8^BgZeXHA;vX(b!yzSpcV)_n8L2|FKRWL~ev&iP8T%jPGSlfS@)rS=29^urG'
    'i+y{&JA{u(<+*V#|FX|<!6*Wa}dEJoynjrn{RrV|6ZiDD2y3O>v%zpK(2`8xwhZAlBmZaPt;ctp<XLxbK8bg;YIBJYFj0-'
    'oNn|bEU<!IEKV+}!lIbNT)dj~Fe&K}SDTIuZBi*fEZ!bbN}-'
    '6LH~x!#d#aOm;X_1~^E!{FQ|^0mC>$I*MmvF;??P#9U*AZn5AOZMxpVVShIT)&UnkeW*iz1btahVJeC+SfcskDhEjae`xlyMd3e9'
    '=qx_QmM(y8vVwNZ@qSuV$g%=|7A63ZZy<8dPV)H0rum12gBd8cyEg1W`5XO*!Y&$C!%&Im?Lv4^~$uy(mJ*n&x$pyVil_Qt8vlR&'
    '0a4kI5oa+J8<Brt=U-j9<ue;X<x74htvhbcG!(}?b=PhhiLBJx%1HLbQSBCMjWm@Cs0eTv0ZOy&3q_pX{?gI8upA_8UIY$$vH-'
    '$ypE#3U-5SC+*#i*96Wd+*0=lp`h`y^??&SyYk-2Udeql8q3g_e9yN5pRxkVOZ@#(Uk5{f-'
    '3!l1g|Ihl5`}eK4Z@<M(_ndQ7w0r(K=e?Evr-<8M3!K3p?Y--z)@U=0RWa@-'
    'j21hI6HA{H&JAv@_zm`y9r|k*o$;DJaE;ENKVjcJ(st?;b-'
    'WIFJ+o7%isSOzqF&qg(*L6#l^yq@$0+r9{yg{Sn)?)w^ec3Q$<N}E8kK0rQpfAwy@BJB>fq)5H0t$mzHS4(&-'
    'd+K<*h;YUSqrLmd~5QKa>lV#{jWWX-$!8heTgzjER1J#cLCyi3@H-owEK~Pgne0gbRh=)`i!gp-'
    'x}CaN)8yp3@l5XgrU4Q)w>|`B7<%?jP^&xDWDJJn!cp<$bpNy5v{&GHx^!9|<nQzJ0sBp*LSV@ALY_Cr+SMdfe91)OM$C&E>W$S8'
    'fo$hP%`L!3UpKM~)m<+qP{>ZOfL;zHbk`9giJQ`~CFkvuzhIp7r`v)bggEJa}-'
    'g?Z%BO)K0IC8U1;6>hv!vGv|L<nceYKW#*i*m8mmES2`C>sV!MH*V?Q~X9rl%T*o?SvuC3-KhgG<#LlMJ9-'
    'SIOU<jk^IoQl+)rk{F`s+!P;O$IuY>R!C@FVu6U0t2Fw_;yP+;LaRSKqmFx975hC-wAfv3=<#-'
    'lyg%*ph2XEnmLIj#J=A=mS%0J8#6xckCe6LriTmcuMe2x*a=u=baD0LfYSb_v7k_5g%7S`D8>jFe1lh3LePp+JXgeT4s7J^kc^kd'
    '5v$gn`1v_gX-'
    's>e_S0u;j`+v@t;*EPZ?90J!eW~{(>2`o{cMO+jnfJtz6aZSP^mdq7}GNSJynR$v$Te+^sLoK9j1GCy%%1<Na~Ulu6ZT(<VEAtIz'
    '|S<}o+yNaH-It3r%=?%b~0ym<?2U>;^0x1rh2Uaxf=$!ypL{>J-'
    'j*7P`D2X+LW(b2KUYcx{BQFc6j{E&@_yJ~aiPOW_L#YfeD|Mz#=|JVQeQ~SUE>z^Gz8ZqLF_K!Xq**;>#sOp$8Usgwt9#sXW<Gh4'
    '}z?XaLtv^@)_y7La>RWI9f3*n{zNmck(O;|Yz4xEh;lux8e*2Nx8{BhLbppDF6DL-tPMKbrPHfiv#4&(w>;>MksJ4FnD)W&Ic0bq'
    'GHf;j`AjZ7V{c+wrFu1vP-@p*SPv`n0T&)66DzMHOGp5;dI8@-'
    '5bM1HVerDS_&oi6OvCrq#Iy$&NtIS3#T2`!BXM26(@_mkr*m|;M^X46HYx^#ko!ygJzL%#RIz&FtK5zEi@tXDP*V^%xyPe*Bms(m'
    'Q?ApgxzxZODW0#{xqx(3{eGVQU_)+AYgSisN_Sz7{>}`CszOc&v8{ecq;Rn>pAeK!{vw3zs^UWug))p>==d#*ykL}xgtWUwKAr89'
    '1`W9TS)sAT{TjqTz(?(oq<HAa}0T|h`Wosi=xhl9R>k`*y=~8$iOZlDIq_ehqHT7pUn~!bqerx^N>~@&E9v_RzwXpe&I>mMlTWfI'
    'WCQX`V<J>84Cr_etbS83siu%xuVYcsg%&@5Qu^9Zw{;Q}BH)+zu#HoS5hyM`+i#U#rpXbW_Bb!g}*nR1-'
    'KCr;9X^oxBjv8&lhHZAOTg+a&J&w;9)YC&ud9%kli&i|}u%RdE)q%aCi@0#%66@35j%)Yha7(<uEnd9B8{eb9E?Cg*I4^kanl&q;'
    'h6472FL2oLA?EQPet2Z}|Gw98Bp>Dab@FkD$6RYWckWEo(>@lt>_u*9=uIX52Jvq6<7_SG_)%WtipE$BHX^-'
    'D>`DI%jF35fKs@j1)2E(ey=F~;Q^P;nvSo+kN8-<b9og%I70HHr-'
    'p?hZ&e?j#sv7ueclR>#2Ea4TkC(>t{$}>IF<^Vkkt3|zi#0m<nBuP|PIye4|83*H?Z1eV+Pdn3*S0M3Ia3_UV^q0@V$MT}Izp}?2'
    'M3P%mH0h1%z`)SHWT+v^=K5^pFMk)_1EdFsfWFI@mp4hT-'
    '=$5cJ3!yR<GXJvV8g4mX#~l+w&gtz3n~^GAH)+?e_B!HpsaOE2QD4W`Fmk6)Swq_uLEmF}~N?+21-k=(8)`-q@Y~y?nXH-raVghv'
    'NGo{)1R2oEqi824^PKaR5Kc@VDf5U>M}z!`rd<yfz&%{ZXSvCG3d#LVSlTM%@w^wPW32a5kQ|bai#N+IUcZ{P;=J__Dq4HIT?1?C'
    'ss%wtf2!>Q{Iji@ZN@j#-'
    '`#HJZ)NV0QF%{<p_$2&Zn1H~zo7dr3p<=;*4=nKR#;J$GN;yLXTJS{wfXCO`}_$J`VnDCIf%J(c~$edAd46Szol1>wGZ{PD*g+gA'
    '=r?sHlFt<=xJl6bv-'
    '{Z_kXavM(A{{K|{`t@7Ge*N_~$1|Tj`&)@y_{4Kq8He`l0jDUi4SYk|bkd`Xx($K9fnnm8TU%I*(h6*NgTGg_ZNcl=?PEeu&ssab'
    'H8!WM_4Bmxrj5SJUaQz2+-z8H=UU%6e#!r+eq7{iGj_o_ufl}}7lGr2e=%l*JJW|5-&AW;{3Gfh>3%St5I-'
    'QMME;2F&xoOzP4>1PIda16_-'
    '*~klV6+qBlr<9?T9HlrvX1Ku%F(@5jdQ*jPm+=!je?8K(&%oCl%k|{(^JS3Y@>k{SD6YqeqX1mFk4WSo33D94_U=o;!Dr{^)iH-W'
    'AWmk(@)0pDC|E_^$AN)&)^-'
    '(BJ3xQGYRw!$tgr9Pq==uiU%$NWzbZOW8bO_xrThn0fs8@vt(FsvnzpVW0n6r>;+dMO=X!(t7aVp;mFbux(&|tv2p>+(SHyjPK{z'
    '4{=%csLC}5zxwH?p9bTXcq~@6Aov}}<~VTk**6G#qp>z;{={bVO&azU2M(+g{Ehnt?iTonH^x2uBftNQY2bv?E`=jg#Gs43Xs&zD'
    'p53kRkL=uhpZoLAKM(8Y%)HEMioHzly?ptb;~6$~IzNk;J$M<9)I7w8z|c5O5#N7(yovAIv4+9p0<VbLTi&;^Utn*Jzp;-'
    '28)wai-NbVXY|`x*IGo!JZaKLP^nc>Z%vbac?4bN`<#LG!$Gtjz`h@BuHO1!w2lsvyT&}wH`(eNQ@^e;O3?F?Q7}8VeRSs%{60c^'
    '^?}3*KcLVzavm}-v98@t<<+Nwb>$%bYxc(ReTBTLaIHp>RvYGG@)#J$cK&c);@a$6E3vm*}|H$}n{+Vz&-'
    'Ye#bgC0L*|8o8M1u(Q>g_h#;tZvkAQFH8h_-byamtc|ZKRKVFoRc5(LVAt8)B?L~X#BQ>SvW4qI1!pii8rMD<lq%0-'
    'K4CBLBij3f3OE*kL;Fd?IkWp8UJ99lec5X4!ckCoMYL39Gu5|@q*Vl|Ni^$yirGrxLJW8T}$=riG_1NfBNZ1AM-h1=1$H-'
    'aXG~~L)Re9wasi+Zsqv1a35hIB|c3$rfk(LjxBCBJ}s_>;{U?mu%GNE46g7)Y<9}*#Pyx=1_ngqIrtH=L1L-'
    'wLkqm<nqxy}&J?+!7cN})*I-68;{3K&ay;q$dDgy{>izLT@0W_-rMRfpDzCtc%KoR^_PUOj`!G%Tpm2}DumJoq>np7}_p``9InuO'
    'YJM07|MC_T|&$DMQr03uqXU|^t_s*ULPq+}@y%cu68jYBB5w|XKI{40Yk1OlkoB7i#@S$cg{|5idu(!Heey{QvcC(g$j@>j*sh_B'
    '3qwu%9c51;rLCX$)ec^-n9k#N^HZ&x*Y}sjhsa{{}*q$}nR&i^dV^_0bo!qWQ{O!8|ar{Q?=+-N*?^XCw9-'
    'Gc|<8;qbAJ#eKHkF<6xzM6ZHEUHbHPabrQ$5fA90clSoD3g4?YJ$r0Gq^r$T2>01nmTP`pn5E%x?JH6@NT?Ru~-jo$I-'
    'ibk_>}=zhbT(ai7O)PCjuD~;9iT2uMHMGn9>4SB0M2U&YV*5n%B<Xal^n7fsClj$%7KKxBXE3l+X?pFoA+kZ~nOYo!n_nE_PnN4o'
    'FuVFXgz0L3s*-n0u&jsav_J%DV)7@5T;U}$S{7pQ`Tn|N$IqzFsW!)RiDZ)Ty7mZcLcy%e^NHLz7UtRZkA0NtUmt}r*Cv12-'
    '*{;!kcLv~>&2j+Bw$b?C?EP%4OZjSQ(%4Y_aOtB+qlkVPTuIljiCk0PfASsl@!9LK=C*Y?IkBoSk@Wo|-'
    '_`bj>nn>F&#w@RU%7HgiYxc@5Ib37dzo#XgK+%#;g<dTciX-j?nGB*{`^_Q?yKNOqeqW--bpmqg!|%)FWNu-'
    '6wSSltf6W4Mf=Aef8PGlN1u5tecZUOsuLzmq1hgFn#X%1_7*V@&qKCxXczGhFeHzAb#!!lOmXGPbsigAxpHke-'
    'q$qeHO4N_Yl~W{p7Rzlvy_uYOqBg`<N^AcT>25xZXq^?uF>4N^Qs?w@L~0nPli`N{`mdsh!Ml9BS(%f8;o*%Xu*Qn@Qv)d<l%3!^'
    'X;g7`Q@1EhabM{-'
    '=8#TTy@G6aD*|=XOjKE5Wo+3U1;k~jW)&YM*XPClV?=y(J_xztBQPl?km2bdPYU9baH)r9iO8n33Y3T?ZffnIk~jLee>F~TraU0)'
    '@_l)<{Eh9OWXhWdH%<L{0CTvVlj%(5l{6!Fvrmt%CT6d(_e|JSYN8loH?ud`R606;Bb>BjdJeVS6_{_Hl{Lp^7zW^*;8$A35GYT*'
    '4a77>^aM9PEGrXX1DQRLhgUWC24Tn;E}<FLQ{`@{G2&6;ab`AId;6RN_RIpjO*>3x7Rjp+Tq$;y}i4<Nw<jmOMjxj5Z~Iod54`l`'
    '*w7yj}sfOfx~rnE}<pvR$do6@=2Y;1s{Nz4A?0c2bz=byz@@`U;p}7Z#<{I3ULVHgJ734XU^m|*pRVH@t-#OHlM-'
    '0nKWs#^(AVHjK=5ey2m?@ZQi`umCnw2H8dfYE`?9B(BpV$*wMe2F6}n|Bqw`;-K*IJht3+lhW&)065B26admow-__McuJ#(|YSET'
    '1UF%wi^XAR<8ryk%so483Y_ad#T7oz(d>%B}R+`<q!H?`WOB?c`l-rKx8rTLo<p1?w|JD94|MD;GZ@>L^`+M)b=lB{NH~I-NLTb-'
    'rUpOK*=6T;CZ{I%WK9*x>K4x-XrcRyaIsT(YjiwKpJ*RlRb;hBhuGI1d-ANlOtsfBs-Jv|}nsgJv5kgO`5_*K<SvuZje#CfS{!DF'
    'mYMadsj^Rv?H%0yTq^lQv7RExbaO*>7Y%aTKKDFIG?=l~lZr`0}-'
    '&@e2DWbSZ)X>v?a9v3_Ai)cC9X9$%aNiPt3#=O35_dJb63=OhAH96}GL4nQ53!jv$Y{J5Je<VkAm&NGLa#1z{gYlE_gb7X9#zAP`'
    'w_X@!5Lg69Xs78=N~Z75&IQCOfg#3Ne$h7kBt}if0NIT)|Zm*it@<v8aa_;CeE(oUBUhEd#s#@sK?}e2-_--'
    '$hnyxG_#?!02veAHlY#gF~q2e=wlFLiMTPs-o!x>XA57HtwM7u@h)@Szi94fe3xTH%-'
    'qL**20YU+J7=uOaDrGcH;d9&#PhFQ>|X<&k+~L4;fRz^sr_0(^}~1Chi;0W9;)>ey)x0Or1KFYvVr#<0uf{b^TTB!@SNl@xS0};z'
    'ej|l8=C2iYq4G7WbDmSHykgb14oioQq@NAMBUNp~9!Yj#z(0&0_yw;+=NA><gq1lsIsqEtL9(^siXQN$Zj01=q*%OS5q;I9;i}ns'
    'jA#|5Zl}4imPtIi&`E!lQkU_?E}&o7vIEN7n9bp}pu$eHfe4crCnubEf4s#UC{uFphCf;$VnB7?_9qyL~_HHDfQ~=dgQspY6N1dQ'
    '4n-'
    'Yh?}`>yf~E5;rfyFX?x_Rs(}$tOpZej@6h8hDqP$yf_!G4<EL5OYpCkYD`W#tBlEZkNAJ=)zpq~5YWC=9R}^G8JFm5tShx{&{{#Z'
    '#_zEg=R|BBt|04U`UK+%F?L?t`ib$Yg?Ylxo8!8lkt1mTUFMg#mYXoROg}4WLrXJOHNJue=xY|?mv9HgxzrrTIbyp^`_tFX98-'
    'G|*4fg1$+dOBrmau-'
    '{tUcfh#0%;ToGGWd`wsl{f%>F4GPA<x$xX<$$d)PE_^J;CeJG<Y`w0nr)MKLA;&Wt{gUBE4H}AyPnUH(6Mm`M({?@dJ)di(K?$E+'
    '8mFw`q%)dvx{`jP`We?m|5rRA-'
    '^&QgB`(8v?AknTZF8CLOP@S>GHfW#wcM^?M)(GKt%{TLocD<Bzd1jtz^k4;gDduZ;%})wd&V7f{-'
    'F7kj}wgB*oHBezRJ3e{+aWlHAZV5);fc^Q~XPDMuo}C*RYdtIpvh+dI9)HeD1bH|JcTyVe(6GAYnqUgA2W?;a~8>%ud68`31fb7|'
    'wmi1;``6cI}e=|7DMhY3x%zIO`f>ap-'
    'r#9mL157cF!?(wrrJFTNJIoa2_lp0O+aM(=YU=r`g*s^*>a*OX5le%UImBi<8F6<Zd#<{tXXu#yJy0R6wRpM@SEJfvY@YK;HpGx$'
    '**t|fgna*(ZEG5cJx*O%R9aB|@1h|eHQO!iX@Gw>7lJ&m)B_2Q$dUy28heHd35zZqwRUo!vGKV=iGA=O{CzsYqz%C!P%8lQL{I~F'
    '$V4PGk!`;gi4QpTSs;(1rEUa6}_kM-'
    'MO!hWUiDf?lwJWkrrHM$u*nH$bmDDyw^xN;NxGGV%^-xqpjzOK&Z0JoX+sEDOW%aE}KoRGDq{)=M=e%TOnR!)Dv-'
    'sIs19#W1g@jEyXM~|Mg^El`nn%%qin@#t%!h7Af?{MpZ14nbtfcq5x&u@ums-'
    'BH-9p$kozeU(x|2?_+D!ij!;>oz~D88+_Cenry_QPDK+Uw#eibs=SNABOkFNwJ-e_!!!=~I^VWcjW>4=lJf=NJ;#Cmv0lo?OuWIO'
    '~;&-S_84X<Xu7b6q({QSo5ul&RTq>N#KdP4OdXbe8eU919WF+bk9<9Dwg;I&Fz#!?EEdVGr?B^QLi7*sS;`1zx-le918-;?dWx-'
    '73YWulrbk_b##Jo2~&@=(pWSeGGds?v-'
    '%GbZt3a_IvQ7ocoqznZkcdxM@QxzmJVsqp|i?jUyU;Rr81Dm3$1$@pkDUlEXlb5O}UI;R3_F;9MKo5YF8B^XHsD$L}v(z=l`65&O'
    'S)@2>N17;j2k-llQ;H^q;XOWDNt(!Cj~W#4HHKA8NhRl48uweU0Vx5|U0{{~*tFjm3?V-'
    'H3Aa^uErp7$m@f^}j?@d&|x;T6Km1T!gkg!trl1GsNF_Vx$hM-BY9d@PaPZ`igeE}UWb{(Wqq^@{M`sA25BA>GaLn8b6<FW9}vJt'
    'P0%q~|A~n{ea^-z)Gs{EzVujPA;n>(OomU+});acU)9;sImXV73_wKgwFlv&!rLXpNlb^=W^}8ZY#E9N)-'
    'tYg4?2981=V>@`^vv8RgMM%AB4T5nO8MSB0Kg$|OhW0c259K&9_?h&zCVr9f}S?{Y+kBN9CIMS$5pS6GX**I^Xeo7suFKk~h$#IZ'
    'Llcra{`f8?g2qsPX%40{`+jHKm>4+o3%ZMCOj|(e@neVbrR{aF7H`mc%9jyF5?1x>nZ>L`}KH1pZlIQA6e@C$c*45ZSv5CkL_4q7'
    't9O87+<KcW+XR00nzr}WpkHnX#$wW*?`NOtPN;M*g+Y@`V)~=cn!jHcEa!P98NK>YuJBXg$O!zPMznu*lBf^q6NA4@<$$mBJ1*uM'
    'g@4d)NQx0sdDV%FvORI)C5&R9!1p6NM-}h(4N1{FizpJV4Qs4lo)?nnPE6zx4)v=TJ-'
    'h0n+6tDrb0f}#O{dS+(`|uy$Cy14S5fKOHJJ<%FAPx>@B>adLHSQxu?)IYomif|L=h}31EOI<@$&$4m-'
    '`}=vYpO$&)v8Z%T<*Vgh9Wj!3(c^Ey~&QU9s4TQ9jv7Tdt+^l-'
    '94WFZ~yjhTu0K<;s5P;jvW#Ez<#Xx$suDeAGwLl%iI@_SED_H9q=P~U*JCUA7VSijfuwxwjn&ku>!?y;qVmvw#f;H<2XfaucE#SH'
    'ltn{d^I>q@ISzB(bS}E-'
    'RgFz<@@%)kWwr+;`ypG;`fuit&L3$zNb8EzQ^&1+jG8*4aDTR&tTK<zWZ)FdRW9~KK=AlA0Oz0d{6pf=ycitv-bXf^Eet<sP$#W7'
    'ssDsY;k*FFU5@M%hCXg_=L3I5}v{Lu_5-#aW`Q}g`Q|(J2-'
    '!Ey@Y?m7eU7m?2U7c*stR&fjK%ZLQR^8clh|EH~^2t)#ZP(UD(sdPR3_y_x$NkfAU6OqmSV?;6&VSe5cUEEHETt*?h+u=hZAXo4q'
    'N0nREAhqcJd#S8yG9etPIu<zuA#DaTMeQmv@3*WtM3f(46I@2ytUFk52pFLKRAIEC<hxKE7tp{wNkTH>nYqX+ldF$T_um;wK1zMk'
    'xt@A2cg`>Wj#&d0|b<~ofn^b_J+y65yqKEofGr?4Mdl;*Si=V1C$^lkTd{EfL<HM|tJ&vpI=(fdojnBi`jZfC)R>$hFO>FVf!hq~'
    'DM%p_YU%uSe^w8vOeu_n_VHtN25y%YL4|4si@EfwwQbA9^A_jaG=T6ko<149y~E)ExQ>Zn2Jz9=7vymZzy?5zjYxWXS<%Mjy{rkw'
    'DN;Gy~W6j(<?9lfZzm2{?9->4Sc!iC-'
    '57A;zAc3a~7PM)t>v(Ao9jCW^?bn#fri(@bSe?3<{3FXwXU%)5xdO(V;=W9CpJbgd%I^1><Q%$<8#d$7tyA_(ij^FtEiiv?Q+2{D'
    '0$CvY1U9L^Z{K9$2UV-uWqn^{xR69>NobX`fJ;|QbG^7=_Eou#J+qR|U`0=AQAG-Fr_sdvUX>a8JWj@_v*WmeR?4w!h=X&>M$HZ$'
    '=i?v!>YefE!<CkVzKWAZsvXyj2@rBUXbUV|h=-'
    'aF{!7=$hW3KtJ;|)W^MIEnZFUb9*Z=qiYFAjf1TUP7Rh<W>Y@u=ENiec*fc+I$~bLBbqVSbQ?2K%JQ+4DY3-'
    'lA%&5PMRtcgEvts5clKIIkNPYkudzF-I_-F}5kLFa1f*k-ns{iF2VJ;un#_=KGKsi+${1O#o*K+=IAXllpKaoFm8P(6f79|M}-'
    '9Hl{vu8w;<+F2d0D-(YUimdkNCFddt>9diN`gloxq&g|y<v}Sk~SPT2-'
    'EGC`wJA?nBT6N0d^Zkp~D2#Ve`?4ZlP1MXw`mVC0c!b=?(8uxpL};wGiKhfUhChO{a^B3<jq&*3GX9Y`AkQ0ku)qEG++)7NqvBfH'
    'q|>L|0b-k~wITgL;%%`v58SdDf6V!K(r3&4uNL_dK8G+C*tO#S)ek@X5W5LOa-YXmU`)(^+Rvze#2(PsoY+nHn{sOM*j26}Dcpl='
    '#-7wRi}42iF1zQCooiHR&^;dZ>{(;$*9iP$8yG;u)jjs0*h<bHwB~DGun%m(7>sYJMk;fta-'
    'x(EmE&)+A&)WcG~_a9Euh$6*>;Q(isR>X&q4zo?M}B_zlP#K{Xf-@dL5gv55gYAC~4C2$y?OL&{$WG*lV&~h8@v-'
    '9ZXC?975%BF+Z>_*Bqg}0C;`i({3xq@zC>Z2@KT7QR$zSa|`phsj!f8T$;~g{<3?0k{TIk9hy)4;&y~PSoG`P9Mc3d`uXP{7!S=x'
    'KMecjmnY_%Pt!O6mIQ~AzGrJ;d`VbIYS@WZ=85FoH{q9Ay`ZFx96HG<S4VjykvHNtL)%n&U5p`$GZ(SqV{Qw@N6R{ET35=JYQo?Y'
    'E6lml=z@S9ZQQuMt*3_=>OSWc9X)#5IY!5ipNY8X`TB(m*rCWLzjp0ra7e!KI3oB?j&U%~D*wJ54{XLaQf$5%e=u?{{Mxav_*`%Z'
    'xrT^?`WT$+c7}#k=oLCoFKMhst*{hN7Dq7OBdRgh2}28RXtt*$2ITxMZ~OPtx50*vxE-;b;`-'
    '9ef`fGO<k>dxIlg=1#PP%#5DtRxm1CrhT71oMqY_6(HgcSU>z58?R*TB<w%`_~IBp)d)qI3~xqj?X=I8|mmoTKV4q(L0#7)lXbRF'
    '=xGrSt&%>{OJHRFa9+!?gEh(Qy}2k*qb2M=;QY<n{FI}2=%bIEGzHMQZJ;2*+@^1Q4ZQ)-5ZWUV!y&oiD&syD-Zz^CZ<TBqhsbB1'
    '``^nn65VNVVQdCoCQ^d)KH*M$9oJ9EeVkI&$M<s7fzsw9jiuMt?b-|xYXgn#6AYhtI=2Ez*YOun0If@0G`!(d;+-'
    '84riRw0gquq1r7e;maZPbTaL8)Bc_j^M$($9D?bT}n8Tat-'
    'K5Ip=6FeB({=BkkwPH6qJ)90Y$$c&D_@u|=%)QhyY_EBw5_R`Q|5^HK~*_AIm$4mfvk$Bx~uJpoS+8;a{y_+w$q0@u9cy5{f*(Wd'
    '}^8w@{s754VJ_>uPE%B70DPdz65Nc#!)Ub#MdqsH?|jc2}xVI9QWPCQNV6xA<hz06)mxx&g7RQ+Z4(AtObd-gQ;9p|3><u89BHr5'
    '{T*M=tSh&b=akt5qb|9p%+j%^<`irP5i(e4WEv~F9g%}%%ok6=soSb<+NY0``e@1yqx?iA14-'
    '+S+)_76Vzr2YN(KjwHTUx>9cYq+9b$%bfaQyqico`H+0?r+iqVh@cCSo?5X_L}6Lsy?prTouzH?jf9p_yqpQ9*F$as9*2<B5)V(4'
    'Y}s_-AcsIJYH6|AF*5T6YMx@6c}8gbp~&1?AVF^e8PmuVWa7`x1Z@PUe~BwgMJYlnYC+sT*Hme!BF@;znwXA9=5Nbsil3Fa?h}pF'
    'gW-(8#Z`MyRE>&4!UO6g$w7~E?v6VcJ}O<RHsJR8~(*{B7fX-llVP8iw&_q-'
    '#1_Om@Dgd*6zgL*>Ce0d9Lo~(YLX$=lv_z4}M7uSJ+X;;qq2snebE!yMb9^J8Z%A&!4~0W2*4jz>!w1qLu|U=C{E)vU^Rv`a|X;`'
    '<<_~e*G5LhFZ67a|<=e?9ukJy$x&JOiviy(l+V|o;+D-'
    'f){ww<+jNA<r>V_wmODMKMqb|t<W;t=R7&q3ak&oj<iMuha!$>zS;iPTW__)&w;=6{`>EfBkaxk9$1^N+lkkP=A6ebuoH1`>;`re'
    '^~M|QC>~dV!OcjRC3UmV1%wBP?|^}9*|NQbhE^FhZ&a&{#`8UU&^OxadR#Pg6wz5k?`-'
    'qt?P(vS@hhtX;%jR3J1<?jZfonS)~=YpZm53n!DsFN_HS?7xG=`<SC5ZR5hM0oU+_16i#9`(IFQ%9#)q&Kv3_D=;2)~XR%jl&)@G'
    '^~6Bv)jf56rF4*rXs@I!2f-Gt@gr$w%IXTspXkcj2O-'
    '9lrMK1zMBHEYPLE%u|mz4+fIwBgJjms@{XAG}KH(}V5r^?3sRQCC;z0Q@)hPAx@k7V2y*U>vR3*h=#naOhBe^2sRkm66rYKKsP$&'
    'J%}FemU_{?13$b-v$S+RFmSF`z!V$2NsTl;+lEhtLpD4hM^i!#Blko>bD1el^U-'
    'L&fa|4&be=J*uZ`ZUBKlYlU}f3zVmb$pBZ<BzcF?*{zS~f$9d)n#b(hs%xm&y`%-'
    'Lc*EPEO?z<z}|MaJK?D6CFx8EM#K79D6)Pu7=#CS5<`pfuqufY-'
    'V0elMI`rv~P$PI=gfS!BPI5V})7y~#T>`iP_b9U&`B>lRGkthAFoVSJV=J=Z$m@j?@?h9_Ta^(ick>=0mJ}vVadc;iZIPQP=mh$+'
    'e6%_eF9#6)$5fi{iv~Eo?5b<<vuJAc>`}SRS59gV^z$2-Zh+oaJ|Aepg6*{qrzlH6@zm--S_#AOwn@?C*4~BcxqhGf~Ofl7Dkv3R'
    'fb4&P9hGW(;Zd*g^>RRNuQFr$ea3sf$(6F07pPXglOkF8IM>!JMK>1GW3E0<0uCni?m?xPZ;h2j5rk497YglwA`}%ron>O{hR`HG'
    '<+ic8O=e7Ih&Yk02Mld+y)bwBa4r5zz7`+Btp|iQfxp3xB4fs)sr{H)d|Bv5cE5&5R>kxjVIbQL{(B?{c?~QFywC<=4vyd^*HSf?'
    'liX59%yIuM)$|=q35i3tm^?!4Yfm%7ID$AAfa}E68`DEg3iOa?N!XUu6m2bgXkZ}ww)8=U3w=~g-'
    'Yp4MaKDcw|uC`5^Hp6+by~y^q&6~HhF~=ABWrbaZxADk1<r-'
    'eff!Dao_qi`cT<J*CR#8nf{Dy01JTxC@vp(P$4SThscHWg#i`TAUfL^C;7CbK109H*iw^j5PZ`^nK6F!D-'
    '(AOA0$^8h<buIG2VoqA=<FYlcc?AwPn08z-'
    '&rnb1Ndq6qp4Wf*<rx@K>zzAy*(3V8QhizcE%raOtmd1KvDz2e`C+4$&;V2Zf6`dv9_PAx@XCl;t409$n>cT|ztO+BAB>kaC;6I-'
    '`~&g{m}`mcN4`oe_FRsmFvjy5JBh!?SR7bLrb)S8xdr$VzU8&U*q36<#<B5v)}Cc}(({s*>W{7i8#x&2_s*A79$~KiDb9{!8SK}s'
    'ANwA6FkBUFyc~ZMewp(J*-'
    'x=|jXvRd1;d9APkB+wInX^+KaTx#+B>uV!(Q@Zjw@VDbCkF=x)!r>D;jXb>8!7ibL;pK7|8SI1F<98)2A;=+Lh0|;VXXxj-'
    '=Rsjv;0ILGN>lKS!M%*Y6CTzBDM6UsIFzq%?NLuZ=yg=ceETj90Q%o;xm%QQUWrRb_E$Z0CN`+uPTA?%X#vzdQ{;dzv%=^Y--Vua'
    '1@F^^abq_ZR#c$49_USmQ_YT)W7DZ_rNUF=}oIdvpAa{>Zq1zcH4vj^aJ#p-'
    'Ep?H3k`b@iFC{X#NX(`Wh<o7}A)Ww?e!0P^zmg&A&3<gkA^ZHZ>}K{`pb;>C-'
    '1!?Xj2f{6$uG%WLl0`1G(2h9vw5yJ9o?9{WddAL;u<EIM(zge$43Mu_skRlg(0-'
    '{8LG{5SF}@HfU_#y92nX8VGK@k)nP*qiWkX_3m;@-`SIm&a5CXEz(}wK-'
    '<DjbVM%plLmPnE3Qn*RP`{63^kk5c4D6j9%U8)5HWXIi6J1OoHpsfcYf7v}SSpCiqbU{>Hj6$KMoVV~)aZ%thj+GPcFusU`T)34d'
    'd41Ye0dQRGnIN8#JvA7ziS-dbL(Irwo&BSx`PeW%d0IOg?xh@sN@`u4dN+o40py&lrx!^b_A3U)*e{{8#ZCcNYEd+<5x8=g6HI>q'
    'YqIDJ{qZ?JfM&il=Ez^wUNg1isTUu#F!+T=qJlZ%{jzi;BasScbtUF7Hrf1_y~F8ocHY3S*s7_?fZIo7ILNLs_2{haRshLr0o<}r'
    'M*4|Ei-U;oxI53oA$H*8GZw=zDF``#PkALSZlK89m6{7AVW!rwTaFiL472BuurarAQpzmWcz{2bp3JhN5xQgbeK&KDH-OF8F7Y@e'
    '9@g@%~Dv=j>-l4{iyxEwx7-SWeSPlWd3sWk4Z_K?Oe&hJ(Htyke6+!t(>X}S-'
    '<;qq3l)71=HR<0q9`+;vW_T_nTIlr~w37$xG9Shr^jQq_4zr;3Zd8$?tb_6>Ddn>qw1@?yhiqBYI+{p2_tY%YxE8Fi)@uOVZugpP'
    'eVzV-K)bPIci_)m0@wsvjRYxz+9m>Z%-d7*yJ@{K_ZBxHh`l#|jX$1;@14qKXd?rp8_#50_bOHy%jPm!Iar%A-'
    'e$<qI^gHmQ$}8}rmN&(Z>@#9K<o`PlAh;sp%<vezqfrSz`s}mO2}82yU_Qc+s;|J00y7%-'
    'CiqdRYaK1&Atn5%<u&l5O5jJeKMFqrJFxFp$Qif$;_<Q^^8lM`#NR%3yM6J+xOQPkqesJ4njHMC0r*j+j2~g^(7Ssr{77~Z-'
    'whk$GjD(&)&7zA5qoc9I`Bt`)tB)jap1;|9b>lqBIzaKTWBU?3*z|;7A$f*75LGbLGh#Ay9@ki!-'
    'lP1v*uO!k@#D}k%qvJYJVVp)Slx<*6#+xkCMI{Hfx3-aX+x5cwCbw&rTe!>C<Ps?_fJ>tx$Jm%a-'
    'jmv=N)*M|=H|Ixe<`FXKnGq3|Q>CxE}b0e)0_L;R?k;YU^BN8-W|qX6T`xG@Ry(0jx-'
    '#6`(DT#XpgK>UdMGiY+ISV8Xo>d<9rz>jME_>pTYf*-Z~o%m6;gdepBepC(osQO3XN2(pJJbC3N=J-'
    '+0J0czw{GEnJ;YZjF3<<qM@LMoT_*>{8GJY*tQs_M413PwXPaFf{`v1-NQT30&kC<~}&i46VW2@#V`ZL!MvHD8n$tK-IaSMw!FKU'
    '~?;UbQ|8m!!Yv&{S$F2f4vZ_S)JLu18%2YytYF#|s6KNmj|XNGyc(BPcs=TYWw!9D8gTI6lfqQzcsk6Lr~XnhcDw3B}3|G|1fF`_'
    '~6qqd>&Bk2|VLHJSSAB`U|#&8|@g!*-J{HV|aEXIYdq+!RpR`E3H=)Ng_#QIga^3qOhf*-'
    'Xs!H+8cB>X72xdlf)&L_p!%KWVyKZ;sSeqUH$Du+&SN*?hWuK#uMBXO(6voGUEq3v15kHpU_<43h7_)+B_i67m&ci(jiIS0kUv70'
    'ohgd4%@W{%SM8u*dt%roA>#m9zGN9c|4qY{U!0Y75T#QGvMbsO*__Gh7uP>b489>4!*;71Q1J`_JU;YZS@lJ1-'
    'MC#q?X=fi>@F;}q1C8j@!Uh8Y)M=@qG_OrJ2xj^|Q((F`xy3oH{-'
    'LP*i;YTg6i66DSDSkvPxzf7G>z|<w`1fK*+{X+*YHfxeF%}PnAF-dpR)gV3-QDDsP(u&S<C+{lYN2l1EAXSX5`NV7ruY%-'
    '^MWVy^0j$cd|w)EU`9E9gw`bcCE~=yJ9GR<b=zMDKg#Me=K6`wpU20f1Hk+1){%cmF2%~=z7;&!--91%4f^%h`<mcK&tC&S`riEI'
    'k=sM_(~B3+ox8>UG3qfT{hrVhOZbuE{EBzcSEVnc8cHSns9M60DuEwWn&C&R%@|h-'
    'U2Al8R(RX6f%WDZuXDV6_fEThI9%J!*S>yj{78*{E)2@{@om&FhI@4IApN=@Ke}*%nDdqT#f#TGzFOp#JATwE{HV~}ywDKa9ST1x'
    '<4Dc;Tbcca#E-Jvy9WG-xHq}%@NXYHxNFw~@Bg6fBhc?U<IfKs{MzeUzXpEfF)Q`sGJf>+*GD~ux@*_oqyhK}{HS#({3y5C>)=PK'
    'BcJ0(Ie)8+AMribjqF#XPs+T6?ZMzxUrse~zW@HN^_Pcr?0EGm_ZA+(39s8>?T^5Z+M44>=U)pyg1^PN=VO0f6YEv@Q8`{;=5Lkp'
    'BVk9ZuQ{&xZsKp{_|c6U+#AjZt`FLvXip!q^FK_zLA%D&!jIa-%laemBk?|@t60L1+J?f9GThw%>kaXvR{5jaKMp^-'
    '?yVVql=HWw^YME4(fP!c5%w`Oesr@bek6RRnf?Ar_)#l5qRsFlz88F~R_X1R^(S8!Kf;cM|9#^PJH9D?G!$>^b?~Fo=fU$>E6w_b'
    '_`UWC(#Ti*BQ)}TU5{pk`U7K}>LL+OW#7j96YC!5k&qXYH`PR9@4`7~Pi?=gqIdM?KmVClg>y7~_;BLY(tQ$7rlF}eN#xr(e~1Q#'
    '1m<Ipwm%{U-{;syfq9@6x6-'
    'wCz?8sBh7T_=q7Og()Z2&=BWdk#zx{suU;grb`#bLp=TX>^+cB@Vp(c$G;cua%leA43qcrAg{R{p^oQ^r2{Uvj{cuTC+WjEEH(*B'
    '#i&2iuvp;sp!6X(YM1uZ0EWUTEKyOv&^Y$^Nk+2^10J#>)9h=&Ch<hX}5$A!S-Xz;pdW5-'
    'VP7(ce1J$r#2Zvs36`|fndoxtM2@jm@@6s^J6@RQtj)VAKZk@~CaJ&wI`BevUOcG%{%wfp*ZwC&ijT^j5jbHc{Na#=63E~g$6`XK'
    '0R;J55|rImzDLXX4aNV*TI<-)ySPed*Wcna7Hnpt){>OZ)qia1-sj&fh5wiKK<akt=LfVB}%2R|!ftDPR>pE(mg$^6>Fg+-'
    '0|HETB7xo)%j?^;=v88bSZ6E}4#wk7Y8IM14du_^CN{#G>h_}B~k>}|{OM6T<bZ_c|$u4=AJ-vxgOtwh(fCr^ewB<p|1xv(Q^bu|'
    'Af>=UVP!QPtnyV=3D&zNtdpBS1dDTmYgdE(6E4L>YwN*iPEO%}#m0egglBtA%?Ww$o?G@HG)7In4Y7WMY-v3>hNZ{SMyxqWY=e-'
    '7TXZ5#DTdQ;p`^=HJz)$5ZdzwvhJ)OlOyUTU*-'
    'z5RB#okK?p`vNqOv>&ta&;5%SP;g@F<vIYwfNbs90)Gt+!MEQAhx(*KY)3V)!9%Dk&bl32E9aWMB{&=STxe~&-'
    '|?PWaJL+PDdOK9ZZrC%`J2~$>grltE3jKIqaL#tx_@BUo4gkN?%lm!XWp8vfA_dg6u5q$f3|BE^||Py>l(15yw)eN=K_DbY&N@Mw'
    'gd0IVE?(gYU67AzyJGxncqzCv7T{`*aH4RoQ=F=X>qacZ&FKv_grg+{Wbna9fPRZ(U5n}@xVoh)rHo4s-'
    'MC4REq@ulWZ0>aBLqs*RdlT%bZsUehY57YSlW&-'
    '!^O@SKDhYrTR9?0pPu2+}@zLVC*{&c)X75m40I0BL3lH;ffW@YtyF9wJ~*a<+IPm*>!$tWAQlfOY3(dZTuW-?GxKKk4xvzxl4-'
    '`KbSaiB4guVwNhyAx5OfdZ{l~vJf+8{wSjV6rO^boA-'
    'q%Et(?o%k0nu`i(LFgUO$k!ZPK&r=ve0X8}}cqKgJx7#fE;Y?^%UO!iys=Exj9R`v~vIYnD@6k@)hsabs;B|ET)sKfhgl>#hH^^~'
    '7-Vy$@{uVQwQQgnW?+73nAPNFD&|3-'
    'pVqxq^nG`3U!e_26Lmk>kR|xrt3EMu8vXI&fO&MC~1qX$XG{J+4%@Ot@!f=R)TjMKfQVUjsYhHFoUmEb71WpR7f|;qqDu(jJMun('
    'I$0c5U~&HOGr&L-'
    'pw*e{z={bH4fBNVDe{ubGCOX3UsweP@zC=U$^d$=J;}7Mez>K8>``(67T6sVgxUegqGJ@q_V3apXLvoadQ{f27(*c~k5|JQcP6`f'
    '_k<_+6L#n7A{<eAr8}mSqo{Yh|%FU@yQt8MRUxatYbn%NM1KK@1-s*s_KEpIy=iO?`)Z7g})MUm1U5-'
    'IuO|N8Srgi`N=rKQM&ul55R!u3$#%*KhDTJ8+M*&H@)8_EC(Pg|A6xQ2)m`AbWBjmDjEK8~G>F`Homds{Jf2dGw0V-'
    'zjRvo==!2u>$Zn)*Tsd%l8!dzCblaV_x=tFYPsPNrkrwdsEG;=ntNU5d22}9vn++ZFb*1PM_nM1LMUnz=<00qZcpGt9)v{`m<fbE'
    'x*V7SBzPHZal|^MXjirX>4U)qK~p}qkj^6;+nx?xK{H1u_OCPX|nalVPAM0MS3s6e-'
    'ke>?WyuS(b(6krc{dE=k?SSyT&hKZRfACA#<o=i#)3S73*rQBluHZw}%)oHBcJ+^z(=_KM(D&=UMEzk$=Rszz+z&^hd@qFeKLRH0'
    '^(MjloN5MJHDLqkMcR^N+Bf;x4S|Lo=@>wBwRqI{n!8wXW$*T$*vs<^|?c&s7m8Jp9bp;K~tTy~g~mxso|6-'
    'y13yP`s+xo3zFLxHWh+zl(qL^yyQ_kXUDCKKu9ZkA{hV6fve$r$zXi_VuCl?>RKV!Sg)=I)L~-'
    'eL}j98jD$rs>X7^ZpQ|X?X#y5=B8L|#A6%s=CbvZ*RGR(jGf<W@Q<Dk`+aq`d=21s#@_f=?2#Np;gK<#*cbg+u_?usqN#Ro(r351'
    '2fLx?;QIjfRoIQOEys_v9$UPad5pe`hTWRLbqfq>*RGvrt3yd!E$8rQo>z@@#q+g>qCc_syMG`2=!X)1Bn;_gHjh8IKKw&)DjtBN'
    'IfexP2>XJqG3L`(xn9OT=3UnMXrO}SbN}#r>DVdepVvNWhQHxkF=wW_f>EcpCjM4vTBlkJ1@D%%<Pv+m%zUnRzICg|7(BMHcke)M'
    'aWf35T!XW~JPX}e_(!%+Y~8*4fb);O`R1z4h1ad!a16=zM;`M-FKow--K{%!?r}`S_DXg8%zWpP&z-'
    'C<h(Y4lH0}?3B*mfev2q<B#ZzTJY*xbGd^}^_Aq)=wmewCUVngXC#(Kop;N&|L>l)T!%WX}84Og*;wD-'
    '4~pTWE7$M<EIvUVqS%WJ=uzrTO~Vdostz>cihwI6Yg$KJgMT6v959okNCxzGUY=OA5j{6iXc*eKWiQ(YCcX7!?S`>95gn)DO39%1'
    'fc%!>V=zh)d{j%0sB4iB*be#?2#Prm>DuB|K2Q{&yv@wlzk&zddhv*-aIaPClE&!LRJX)M$ltg#L;{>t-'
    '0M+_}M;`!K$SoF!0XFTS7{W>_>w_ZEt!GlMx$3{HAz)Mc5cA$^@(!!F>2Gg%AYoiT<zxiGT-YsLJ>f3@P+4HF3v_Ii*%-'
    'zDMg(p$3@8Lu0<bc^x(+W*P?)lMZC&WE!&2=bcKWT`?`{_IV`^lqGf2P1Iu^sw;@Vda^uoL))a3r`j_$GEfdh~4Ko8}s6jBC>E91'
    'MROEN)-YqjS7L_?z}B!ZtWAHWJrO_*+?rt;lh>=-8so7k-`MNkt8|lxI-Z|5Lp)>>NC#RLckb$?!Y38^;Id<-'
    'alwKySPTBgyOh6nN7)x1Vq=<zPe~tpC0EQC?fGbdOTYbyoA1>nQR&%};@AwcfaKQ?*i4ZNVn>%kuv1w$z@yczrVQj)c1j`!#=a?M'
    'XB{u^;}}uMt?ZLi_njgRkX2^eUdwtMDV%YFX{vhBchx(zzbCu#n)^q+E;K7J-'
    'HMzPZ?EZb|l24q4P0X^R{~j_a5P@l^Ol)R{rIyTE`(dQ3;PX@qr@pEtvgz&--6a6D-E@K1<kc?=n@$GUaYed%pso-(_mF-'
    'UyB{XhQW?e@3c`iuWozyIKaPaO9ko=qP8@ZlpG?3eS5l!GR_<#uGRAk2gQrks-SKi}^~ooe5E=KD?d8rnB;jM#rC4p-'
    '!gGiSN|z}vvzuqhl7n(SD{-kRADyoYPXjvs&gIdOdFd-V2xO$^ZSBxw`PpHD1!p<`{>3cJC*;kUeJHbXzq-'
    '{Z9%Pg?W?@V30kcFfD@e5kH(o`<2@KlmQ;9q>2ib@sW$N<tgY^KgTYlyd4rZ`+S4yoh_ie@a`Px*OD80@qaSn{netH{fp(KWk{hF'
    'KHir^to&N5rei?fy)J-0DSG^kH7FXYSaX;D>Zj6d8{kJ;2dk3HEV$#AHVzD`3IkVI@;EI)AAYy-'
    'hXp{Q$OW%>Evsltb9K0$wPzP?*VITY-axF+V&C0@cJWs5Bo`PUp3cRE0brfTG-+yGWTH9s8ixNQfMwX=Y$yV`0*3GjT<-'
    'KIRfBr1@>0pZ!|Dn^TUeyj$^)HBGaeOwSB_e%8VJrXy)0TzJr=H)^C=&wiq0d1q&8d;4RsAtY3o<%=Y)GLA7kz>V|skInEn)O}0`'
    'kF8U|)0gv$Z<$u_Pu}m>y>`X0#Qr#K$nLeM8<IDaKT-=(k+u<UBXPDoBdHA@=u@(PeP0F5}??k-'
    'Y$0Bf9`V<)D$dO+LUip>3N8@vNmBQc5r#zP5-M!4Naf6-f_Li@|-'
    'fQ>lYsZIpZI9Nc4mgekUbK1hde@WOx^=UEXXD1Tc7B^u?wI%ss#O;GSgP~pE&KrcurGF87w(Jdl!1HGPl-h_CNfWv&)Fo;o;Zo)?'
    '8Mwhj2Ka|v5q*uW0>qI*>|(oQGIJ+M}ZND-(=r|Z#b<Y4k|X{H8?LgCH8{91^#BQYhZAUcW?%mFE469lP3Z<GOq;>4%h#@&-'
    'as&!{~h`xVQ}(>cZc&uGJWaUBkZYNqh|d)1UstIOKae;(1Y9&SP7|cR2>XVScf7!eAQz&Of5&I{P0mIQ)?KYSjI4>`nL^ai4f}-'
    'U+rIKYoVi5vWa@CVLgSf7lIw1M8qqf{nxDf&&NNGWgHl2N~b74UhCk_7=n#ghOKsY|2<x<j5}@pa&jx-'
    '94TQhC$pfxL9c|K@BeEM%EPI-^%w@{WAQ6y)?M)haY~(Sm<#*^XH-PBafXaKF0XT*h_8#=gaj8ha;{?KL($iI(3Hm+BCaw;4<KD^'
    'HZBMXMXVC7Pt;9zK1Of|66Itgs-)_7CM*7hWKRQvOZr%Y|Ud&!FTZc-3)(=e0b-'
    '1fk9f|ax9JdfLcFbH|&GGgdc&$5{HO2gyUg>hu}w^Q()hB{Aeit(SrvMoWCO8QJ&KzEnwa+Y`M~F8-'
    'XFun^)AF>*!eEF^_0&Gja_I>~gU`Vngsu{BZg5B_0cg*TWv4#=Rq^MNFSHeBjt#XA!#yTe0g&`%=|FP`{1$;2t>liTI3aYsp^rdt'
    'c*$mqu=Y*TJCw@qWa<+}Bylpm#>B9$%y`{1CBCuZ2zjXAWWALtX<h9~yQfZpksZ4*E2Yyk5AFSjfV}kpVYX%`#en`*sHgyxe{}8='
    'TwcyU;yK8f@(G6n9X}o;e_JI>%%qA3f#nC<elD!j?XclEc8<ihic>H?VSHt@r@gn|Py&fl2F*dx{V7d*V9OkphQ<BRmLSCB=y00O'
    'hvjJ!-?N#uV!&#$nd#8arprnrZXVRP&KpwTTm_*T#>ZVtwPQ+LvEWv+pgi{t1tcT34G>-'
    '7OmYlcM&`ZLiBDoh<z~^Wpvb_m!`k)?@j;fbo*oTJJ@jW5?g{-{9p7UrShP)Z0=lEY%SV?z1?A&MjxIfTK^I5I$-'
    'D<Jbc0ohJDnuWH1Fd`%8d3_qu_?;%#n7#2Bl<{$eVn^Zg$A0zG@KIePeLGVD2J!RY@$B$UI3d0kAB%X%q!vv4Z$Isw0cpc5iqe$^'
    'p)eRKSO&mV#7rAVXBjO*}9n4=ku{<)*5KqUJcE9L1!|a?De{b4K^^cr)M6CYl(_jA({t<pIE)6!%YG3%6h@G&Ta?p6pv2)gX<U28'
    '!f+G>HW?o_LpuY%%!*0x7MSZqnu4JB6Zb`mQXH3(2TaP(MgwG@Qt-%+04j1P6^QYdxmYzTV)!*yKL|)%#^M=idYtnBS?-'
    '=(~*N5k-'
    'tB~i1gTLX^_#Ef0nr|^r`#J(%w9U6Ee?akSVdU~X&6gQBP&y|m&a4=W_zF>9Eb$eT%Nn&p0zWEp2hsT(%0A#nKm72c>s0*w^G|hZ'
    'AQk@U_>qs7j9XkMej=Z@b8oXg<@MhJLvp(j%a7P*J+E)lOh1hAPc@~fy^79-'
    'ty#$Z@!SE`MP)6ac!N00;@n1GZBZRv#b^|3R(^xVhMfDMx}9aMJMcSl40rC_>lg=o4)CKZSGcYl9`_^OM=W~Jo`cp7xJKLd?R~9%'
    'efu0!I)40E>*2$PT2&tnJE;yiV<UTX-UF9o&c)Y+BgI%Z0RM<QZ^w^VZ`k_R*Z7R>S_2pPa|>!^{Y1sJq&>;J8aZ8lPSOCRA1fz9'
    '@d90g@XMUTAUg|RBCoZ;n+}=H4?A|$*9U%l(0u5S+iK^|J!W5YWr&0AY2`C8CF1wQTEXausd3Gb*Wz{}PRY81&#(nHBCak@P#!-'
    'O_Mx#)+&SX*#DlO^makV+-ePcfQ%(zG7~_4!@)DNIx+Zd=Qrv;@OLYJ>ww2@dTB|enMZS)&m-5f{?}rO_AYn-OnJ^G=DdP1!KYjX'
    '~*FU;>^S0UHu5-'
    'AqUcKpDIbmhY?f8`HsYr`YT&f&@E7{NePWHq0*p4_k`&sebv5o4zGuKKFnEeX<5+7&X%Y9@V<^Q4vU2D`;(|IPI2N<hrNvVcZzR$'
    '^XMTC!(<NKNI5(Wo;Bs>Hh?wfBex!u0|?qU7MA0OB6-'
    'TU5gIdIN`|K|0#+;;dGk7fL=8SbX|eLe<aOVvCAe~bE~i6?{31hG1BB>4ok<`}Bomvgxa9MkLMxD7eBax#?1Bzz;skYq>UN7@6GG'
    '4=nyy7TPPt4gl_hw0UC`dQ5f&|1BgUiyvgah$Quj3+RLAqt@YC?cT*$`PfOS^?!&LJ<@YNCHF_K_DT(gAmy;gfWxWzkd7FzJ0pY5'
    '&~vy|6iPSpZwfgw@#fpwX1fWI`wRW!BNwO&Y6o1oCu5q9Eln@26al$JVOtmr#hc{s_+nUU!6;A95UC>OYqBY!i)xBXRLSbv8?`2u'
    'ImC@GR6${X8j&u7aIGJdguM1Y_WCH{3tc<>m0*@wVD3hv(GY5q;t|W<GIL+T0zziYP9H;SMaxUIiF8g^BSJOSNn11R=T6Tk8!1|#'
    'V-d8Vg&4i6*poKgJTboYe&m#YF$6$-t?>)x!yW=%CeE(8ISb*<+1T|K3D3@)rVF4Lvl0WJi!)IgFt-'
    ';G5G8;sgZrvJ(Q!99Jqtj&rAzHg1Vs@<lBdzM32-'
    '`H&^b*8FZSpN3odg+v$P3L$Q70hvt3CdK&MasYe=m+iiCYz2%nS?kBEzhu6`XW5vFlduaQyv7kDij<waYL-'
    '&k{qRY$~bj+VO_GWHvIO(|FyYIeRz7z7R<#rkQT@gPbP6W;~YSh?vu(XjQ$FvV0ekZsG^&IpvjB7d^cE2~)#%;pncJAEUK4#3s_K'
    ';0{{%$ZM)g;lshFtWya~BOAK791hn{FC5^yZs~$rq_)(yteF`oLYz(=-'
    'nd&(SyU`MlO*M=d*Sr*+IZ49sKaz>o)melm~P2gUa_7l=Vn(?Q&f>+h>2y8o&NGMqjg`ArgrMz5E#WA6zW-'
    'h~{IhdAnX@7@=BcK}{BVf3+ngJDv~g`6cvYTtOyfcI<ED6rMZs^N(D<!{vZoBd<^aPHr3?9#H!z70)XblPVP_7HprUxye0y^=z|y'
    '38eFAH_T(JZ27)7iX>j;)ld-!7jlt!7qtH5{qPRTK6s|!<2jI+5-'
    '12V;&PrbzdXJqhnr5j?@^zQy2229!~ND?*y|PJ9ZNC(mg<Syv_*Sz63A#sPW6bei1vnoaaki5xeYu!uGRV!^HgLv&8L)2N0)C4n@'
    '6=kLdYtK2Wc@@Zpfdi5yF={5HqV6rTlKXFqQ4?<<X&GpT2q$3PdsNmPRs^R@#VZo-6n+o&s?Hf?6?^JnQeXU@W~{Tn-CzDfs~!_<'
    'HA8^{ltg5|~UHS)@sZrz)t;kvOriCuEtwO{P{o4MDjJ3!8G;>23oFLuX16d#GtRr$L8YJvNDuRbf^0IUu>ia$lX4WAWEiM<jraMy'
    'f!<T}z;26k|+a|qhF<~ef~2}2@&>Y5tXhNVl18TN>el68XmF7S0YKEd2sLy+OTdE}t?_%|Bvb=MKrI#;-'
    'X4rWZ|q<VV3@(OwV@Ic{9z9zl#-'
    'i*C1dXiW&x`%!a+S4F>A>NnGi|aPdt~dq$0JS3gwlOT?z0Q>&zQKA!{1%xJ_h!vzfW`F5a~{{rdZ9HS*Hp<1`5`MX%pE)Ey>U!)7'
    '>>zO*Yz+t3armzvyR1Q_Qx8FOb)9jTwh(cY6s<KR&^lhE4>zL{>z!q#2%8^7d>yEC1*GG4=1}`dksE_!r=`69P^VkBx4b(Pq;Lvz'
    'KP``bJZ2lTZDQg@`l5{b<CeXUwa;6GsuqEA{bTZoct{InBWNPKaE{khCD9yWJ@~W{zGQq<H!x{Bi2$qX5EeT7Cz264{~0?eoi@0Q'
    ';$!cd{VW#$Bx0T_Czy|A7@=W)$oOT<X%4P*o)K;hAhvAuS#7$e(KwC?~lg4T-'
    'bi=ts`ST%!>ane0`b2kKJ!2e`lxpJmA5J`FEvQ9Qz*D7scRn9oBxE7=`)2hyxLO<+<bZ#5vGI<Y*kQ)DSLHEZlN)jtjNZ<QQz(vO'
    'Ufde+(OPLh?I&__2)N9E*8(6xntiIIyn^KAS!crAI>s`@=5=Ls^SItC8|+d|T!rIV|hfZw;TiJMP&^1~#*O^yqQz6DCX{cO>lX)D'
    'GwTx~2i&o7fuHAO3g4aYZi26|i8*ksJ?fsJ~A<o)|y)7_#KIT|<H#iD&cw=2k;y92wo+%VVrz9S{bGy#r6e*CY30#}48i`;~)*@B'
    'Hw?M~LUNz&4jHTOEGG`miy3V;}gWd+@flY}wj!Uhew!>zlkq_FTv@v7`9U?vB~BXSIzVKehelo9}3c!*kTAacvVPPE(%Ev}v=+pN'
    'V<0u)#O5>D+(j5cWIP$PVV4YfxjJA_vwE$?;0DVb&UQ2eB#mj+`Us#+r?NB|e1A*e_u(8OGTyM|e4xELj!$yd3<f1N?~N+__7HDK'
    'U7=h}T=|*Kg_Cxf7fJX#Cg9@&6ykdHlZWZS#BK=d2mr%eWSu*TDKq_Xj$0;&|xlLHT0T&S0b5YjMR2&asTl70~O%`tci(8M>17Xv'
    'XqY^T%2d-yv=(?x`#A|6MljPQ3=PAJ%8|0$p9Uj2f*XOXh#Ukyf?L2MV@w@ZbUYP{d{nzlZit(j)f5Uw-+;W&hWBANd8u^U%Ml-'
    '+R;V*zxqT?|+&)4(g0m*Kzdd5#@$F^2o#DtV0hHzmN5Ofou?QL}Y55-'
    'Zg!$fvk0e>jcZB77qP4XV2w&I9&$k5T^P0=f6>1U&+fZeeJ&|hNSz%?>RR&_e-t^Y3yRnG3VSy^JSz@D;`Sp$34QFw+{!a>-'
    '9?9q2T|nee>&U)^y8OG3UW%ySv2&iTt!zVZ`^ku$lNyhYmf04{(j=5Jzy3g1!BgdbC*Ae}B!Np-'
    '<G1_`Q&MsSPZc=BcjS<4eDscb_~tu7U8rwi({v8}~8ql5_LeW0{i`om#ifx<$U>=Jdf!jVAU79GiKybm;>+@_gmW6{@?X{~dKp$p'
    'tIFlYAZadHCvZkA`oAUR|c1@7u}e!w)}@T)-8W$FYuTP@^C7sWawtC%6GJ;B|c1<HsLw;?Fg9l=WN#xon)*Xg&n;x8!$GM-EPcZ-'
    'EYB-'
    ';hK41!3PFl79(5Jbg~ruiu9674llEv2Gol%Dc7K+`k`xfSjBc<3CI6#+a#n@ltzqC>}qpI5KfSdcuG3!6#vdK2x0e^UuE;^696)i'
    'TU-BY8UX|Vm%FcJQCM`7#~DFNx@1^bm6b8UArmPum@W`J#esYZEf4eIUNXjHlOVzPD@<-jW>vezU^AKAp@{W$&Wc($Dr6-'
    'kq?1RB&W4--&hlx^)2&lVqUJ6PsMuQ+q+x7DDo*|zx*ruzvG8K_0)4Z7N7K#;%+BSfH6NMt_t(-J7$9&Id<%bu8A1_qmLdJu2$-'
    'ePHEt?fgQ#Fg#CQD3x5RPWXqPFU2#5L_$2W-'
    'e2pD(ExVAd_7xm=>|oEj&*vRFe~8}_zCuj<?YD^)UmWu0n*{?ND7%!Y<M+y!#2%t^<bfhH)?4;guH$CSaZd~KcS@`Tp1|Ia;|}>y'
    '$c%G@Tc2w?dGcw=4tcR30!u?rkYRZb9;2uG#iqUf7a78h`b5h7X<?Pbn!rJLEipNLjyM#b<@a4<17<?}pZt361D_{$#d$J9=HUk%'
    'RDUnx*5}U?Tc_?4+5Nh~&@D69Xe5TIy%WAEF%B?Ya#)zBypC_hI*|2)E%)B6a>!b6@UVvrpT1T0L&T%uYG&;rm*#}_c?=$(IPs*$'
    '$&<vd7{s!`M8w&t{St%MIdZ*y@_R<ybhQj!9~ZjV>G#kf^8``@$6O?y&*zb4*{eMx89(<NJ+5AsZFu+H_d;IC51z4i;`r;PKFD=9'
    '?(syNm|pgdfum>GHuo>K-%-_H%I{{l-Z$5ZkmoLqy?Y<3_?$}4t7FVnta-qAy3viY?|h=)NZB-'
    '>Lzm03*u<1$+N**g!J|lB4LC{ZHC5_v7~q=J%DwZ>d$E4LKjh-'
    'Y3t>MmhFyJMBY6$`^~gf^TziT9%n1p9P1e#I=WSwG8OPT?EOk@y81QGu<O|;Pw(!b6j19c(iGH#gi2c^X_+-'
    'J!pRD9|GDn$@$jl>UDP2R)&@s5`s3VLad;=Q>mgHV%)Mozr*B7ZR%mH@!zWD71!;3DhPdnT6&8y-'
    'pL;v9){$c1}{ncL${lO1@K>S1N0zNH!PW<-NHTe@|-9M<u_!!93zJ~D-j#a$Bd7k-j&8XK|$G-'
    'Bh^0$advG>D{FcRO&nCMI&HD~ZeIg%Gg?11;N-'
    '3;P>W5(PQKIgKAhmpCAJzz~@UBPa%_7TV8alEGZK5<rTBx?+N=T)oLVxtsyC60Rc-'
    'Q%@~%zQliuj~!9UpIDc`DN~BlM8BjRxy3`PX*gBu4{kExU=&g%(Y^_$-'
    'XDND$dF8lfl$x|5(XRNAgd|(dIq&j@To<J8|NKSOX`;m=TYsw#bLMc=1EkAA)%@&qFVz`*72OC$SzASD^P1F$d>L7awg4@2Ph>wM'
    'o}qcSHM)H{ROt<$GOVT{ZW49j|8~C(A8!%o^W^cr$ei=HEnCRnJ7(5av0teB_%k8S`FrkxxV1kGQ-?g-'
    'urR_?cH6$dCMMWI1)}w6<~MCb!*r=eV{JBkpRu<Bq%9Zohq0$E;cNLkAv~9UxAH%(iUVA$<%#MxVd==HYE%O?)5D#RUr<K&HY1?z'
    '(Gy`^`7s4o25t6!`tfq~<tu?M%j=nt91wtnfF<jU#JP)}J~q(TPr4FNvf0$Y)(Y5B^3Rm3=?gO&pcHesm6*pksr{^75F6<#>O{ac'
    '1bt6t1~#<jA|*h7B9lao>G&BtQF&*jwf_YYX_><jK?9h7TXzcK6*AWA4}E9vvr6oD%c*Uht&L+B0N1*svW-'
    '+`BX5&J91Z?JThXK0}O!JtXrv^t{ttE9hWyyLTpMw)CI%iglkHYUFsw9d}Tp)HZtb=(e$A$LclDRm-'
    '*>eRCUqoYnA4GQt+d9$=N$qwr(UxfXcbo;?Sod(7kTSv%laM0VrGO=<>m;|SJNjZ5qrdRWWR!@UwRPg=U;^~iY<&L>9y%tuqlrif'
    ')2KO#1ty%(BTg?l1+zs<TpJewFpa<FzVHz!V<*nxf_L-VHB@~g-'
    'F_s<pn!MvL?<vwHs_J+UR!mfp`b;Ntj>CpXI9W!RkW_?hsmAb)LCnPKI6R<gSj}f}ZvC%v8c!b^4kr+JJXu0v2btHALGi{fyo4M>'
    'BZyDdjo-we6m&BWqBf6UUso!@lmU98QKhE`XP7ZuY)Q=%c;uq{EiIp+%`CYeD53ZX5w`s@$nXs0&z>g9aiM4WL<Nve&+q9_+V*SK'
    'eiMuXcx~gOL>_s8xh4H=Bv9_#@HDaG+h3t?G*Ikdq(A1Y4d124ECa<OFoA;_<>CR{IJs`dq@<dim4L~i+ufP6Uc?$d&_YofxzX`r'
    'O@OI{S`l;I6Wlo)Z)Z{Fa3>|~E4^t0xi5g$V;>F8_hp?`KSH^S25ZEgpIB-'
    'a~$B`qCX+O7j@8R^_PsF($h&7dX037!FV~%6PjtM_<&Aj`~dJa0SYJbsre7TM`Je_>j*b_B|tQ9<FuV@_tgF}Xc^nz>ROVp)+u@U'
    'nhKYn~itR2cr#{VX_2)W?{A`{ohIj^5s5HhU%#AYBTWCpeij>K5KdVTn5<brO|{+Bon`)6!m$!9$(S(dmB{_2sOW7w`^!s8Ad5*J'
    '(}8_U3a8Rj{6-Z}U+>m+px_^2aCj^tW2zp<Ige=WQSU&cL)`9AjmTS&ebH7Qq$(}5om2c*{&x(I%RFB-CFF;7#kTCSDB-'
    '$!=LU*1C>{T|ptExYhPG<U=92_p)BxeLsw>>Zy_tcSP<@tAmDzI9w*C+j5rNL;IM;J`ucU&B6YU93mie#x8bVBgDikekXL5Bq)h-'
    'FFM8jU%|Na3S8u-'
    '{xA$cggxH^<cs#n)3&JkNYKVuy4YT*dKCl(P``lHj=r{dcwNG{)4(Yj>OlHFS1021&1rON7Nh{BZ|kZuwkuuy|rvvk79w{-'
    'Rl`)$M(lH9~O_%;lq#9|Kgh8|NeL4fJ)mVtOz@k{BD=vzxX5IBfO72A(w3U@ZsTi-'
    'Y&TzGyL3K|73R@56qgnCZ8~m>J`O0!Cb(Gf$M~hbkSEY{&QfB^;N}_U5|iIPEG=QrdU5(v1VwXqYpf=q{Uto%#S(+>^yeXxg*R+V'
    'zlPJ0?UFo>oR?7#81y&gE_&7IWiEtly7T4f_y7%6895d7Td)AHkMu2?r}t3#Ho=xGBS3HKBAZ4Zn?kav&=_bt7VA~PVE_-'
    'h2N!yi<-k+r-yv-'
    '!G~Akti7u7+uwdA3<~^+^%DKU9wUGDXJM;4$uTJT@2553ihBO}qKo8ZAWQsO*LFHThS(|cKt8T(o;Po9%#qnKXXXh<T)A>-'
    'qnpenunz`U$nxdOLYAvE=hv=9#@#U|mxqj3hu!N5-'
    '=`N0V#t{@uQvD*bw;k+qV9<Cr$7DSdt*oR{`vCDFJc~iqI_hp2O*1ieA@L#LkjobTN%?*Uz_wjv`6c#@wc+CKc@aWHBS|Jee4miZ'
    'Cv}BHR$p>$#B&w>bcg049qo2PQq%*kH<Yd-SN3qlGTO{>$IkB-_Aa}SMz)C-'
    'rZV{_Uw7c{$}T+j~*TJ$tNFQratZJ<wSkb#~**x$@PF2#l7hSGh)OXHg=@>#~|mR)YQBXayu9DJ0CiDR*&C$>kY*SFI;#>`@enr4'
    'k_=0_1o)s>6i1Aa)ZEwv$j*$oZK2=BR7QXHpmwsmkS?s=T35g_sBmb?}M>y*;@IW<V4^zuy5M6i*@@*TnGLF9CgR#H;|8lKY<^?J'
    '^?<uW5-'
    'U$y*(A@e?I2r$HI?3`|R@=U+8h+3p?8hUa)!d4&qV7Qo6u}4jnp1Es}Wfcn%h_Zr$dt4I8#;z2N%6j*c9mmgTs(wN9LPPJDU%@6%'
    '7e5dRAY-kU>Sd+l7v@B9#AiRaGIU+FEKGZ+upf#n7+@#K@_!k;FN+ydXVKb1XFrAI}V<jcz+AZ`W*N4#v)re5}z@=;f;Sd;$NR$('
    ';{Jyb9<d<FiSdq%9(_mH|G{MdsBnFA+;t07bT+8CYjz0P>viF}Cx;Quo4h1nO_PwDA-P>;L2*OAL2zlA(<{1Sf$+-ToE-'
    '?L+##AS(V6PJDEmDd{CAuo<ac7Fa=`rRkwD;C*36OT_Rp4i*FFJ#lxHetfJ*cY<aE(m#$8}&e((~6J@_G^>&Jjjk~A+7<wMJ#RCu'
    'Dx-+==O18NBCELxZ*L%3p|Z;ec^?dGyYs+(4Gg#lJiO&By{Pdt`R-KZ!>1Z=lk{!B{qc~@Sofx^o0M#-'
    'vi^sZ{~c_L2_R3ThR6FUlacRJE30}hJcH_@do3qN`~h(7hZb}{OuuOFIkI194BP4BlgwPI;KpS5$nO+kQ@AzYtvS-'
    'cVZ5chqOi55%NR-HgDb~-'
    '69srePu2_`Q+28f#F#CXbDpaoq95^|0&h7ArFqOZ6hw9{D{e$_ykyGXQ_!PxCixHd=43LADFv+G5?bd#!1~_!8)JPy+O{04)OWNB'
    '>RURA{P7z_JMeR$b@=T>OkI&wc_27<J%!a<c7S!P~atdO}UUSzkDWqjrlRJdc*;+W5@Q;r?px?=ggTIYvmI5ikb%-'
    'HV|WEpGto2L1E$O90Pl{ZQIUxeNWEKhjpLPv6Cks&$@QiX2-RhPz=y9Eab)D{E-'
    '*3%4=_Q(X!(+$d!Q{eMJ7AcXfRnIiEac@H)eIlSlRoiha^+A+ORyFW1<HJC;EYIrdR??>*}A!QJrb*!!@5Bwv2ry7jG+zk+|VS#|'
    '?G%bdB;|9#Rg=01b@V7c)+vSTh4?AG#o+%cO*e&zU#@cvRed8)xH(K}<m$j`dzx$A+<T%!bUUFpL`Kf$+!BY}B<Ar-'
    '#B^9^4hbMefXH-}ujNZsXoS$lc0sYSB<h@msgq3S%VtPL7^-F4Ru{pnACI`rTF{ogsZ-'
    '+1GVZSdkC$Ks!?A(k({z4YKc)NoNdkKXu)<9Hs9R~tiO7&jU?_&)wRz9zn@`K0+DIDqhLvbThL(h6U2-'
    'g?CYgnyv;HSs_2qw(YKZ5uUeOw5z*!qb_ztY6&s{rexmX3E|hJ7TZ~@|<~wZNi`E=~*vaq;R#ZXKfVz_P2lgw?lvQqaO)3cg;O=G'
    'k-Vnff@s;hp`aviE3W&fn48p57C-4-'
    'k;5Tqu3NVnDAgBC+C%C&jZQkuDk9M=Tr80SAG}sCpq>dyBRa4D&{$9(zLKgi)0tUj|yM!bJ&;0Zy@)>HVN5*i-'
    '5t!{8D}@yeG*cqnz~kP5o}x`)JPvPM%yOP0nocJ4pYC2XbU&9d{GEBcA2@qmn;;x``E<d)l#m*BP2qyY4Fr&rj@Ag`tffKVGt`2Y'
    'DsNLWtw@8hz@CXE2EG=Uy`&-=ms^7|L4+Us3V{Bc@(B=Ctw=uodK-'
    '6rW?a<b_;`pW=sM+p%59x3_l}bzm`HuZy{RgY=#~aqh`nC*vBBMn}*M>zd~*!?|wQH*A{iL+0~0^_kcY;-K(CBz`39$&bk^v<-'
    '%%B6F7dVQz!rZv*4?#PEr2AY1TDYKQK;b9~$A(c=_zA3uIFF)hgq*@a&tnSsAyv%_z1gX8bU8*ghLHf$vG9t=+STgZ`^wd&$-'
    'x@lPZ@ZqBxIUp0{V>@Q90^24(uVeN8oYw`8$q6By<Cr*z<jP}W*~l8Xp{M91JhtF(<gShwF`|i&p<B)`sqx8r48()|xDUewFPRD^'
    '*?#M-ceG!B{msZw>mYt2_K!7?b?NQ5-'
    '=RhmoT&Y_+eWm5Q+n`y#^}*w#Z3u*4*phSZ&{zB$Hv7iTMy&h9GS1?<94q>29L9*MC%xF5HJtsvg16KYvP!SF~bw!_$T=X$PdhI<'
    'j9f2;CM_t4c)Si4U}80m-FU<AI)#@H?X3mOS_ee6uygmeD->dKNo-VWPE>qJ9sg*gLmIOL3#`R#u02YYvH&LjXldct}c&(7@YAV<'
    '8SWw>H0VK7<O&}bCde5f$`?7JyI-`b)A?T|K(aP^gTH_w9aOILM!<Nlxx7;#y+BB9+zU6*3YK?P4au-ftB)!!uL^52ACUj6P#r3T'
    '<Um;$u3ZR7JPUUCQMbm!M*oV|1~@A>GY7}WF7CjZ$YhlUD+q6i8ESmHP&dpB4QKxZ_MeMV}tkjF24acNUSf!&jyVf!4trJ@NXhh*'
    'K1`Sd-5QcTqW|2SzpK@#y@raf@8I;+1O5Sx5D`|Ip*&iVVH?O3V$o{j!lvovSW_`CPFP{*(+?-'
    '{vCXC;ljo7+e_kei^IMw2pP|h`9ZzG+OV5Dgmb|^#r1kEO?~W_lYqR;n{Up2*3#s<k^Gzk1a^tvLtZ@`W#}P1Oki&eu(%3`vmEvR'
    '#CGg+GSA&t2)R;A>)LMCo4UUl>kd8yBl~`-7GU~x))TOiCBopqEQxDyT(V?^_6A$G?#SF(<;-@0r(+x06Vm6+J%gOra`-'
    'UZEC=FRkIIf?lluC`zS=KO3;l3?9LMy-B~yGA=5W;)T-'
    'VHJS#vph{f+;@7G4p9gO34U4}3gqT^IO5VxsZ^!8eR~ATKZu<~YZ?j;7>(mYSrcOM4_MV@UMRLw??uV*g5xaoKCL1`}%_o<;28=+'
    'Ps@AR9j`b7NcPD>7DzY+TD_49+!do<ppY@Yzx8F>Kf{=8gOx@SVgurO)^%#_h}rAHS=$1pc>g=yyV$kG{{jVngsp!Gz(IO?*RgWb'
    'hcjADMz78GAvV#JRzaz>pR#S{`y;q2v7d544snS*e)T#*N#%Hf`FW7|gzXhZOf?pZ&xW&&EFPy&=E*-'
    'Pc1ZOiTC?`yyiTabB0;Z@D&hRlRi@-'
    'DO{ZZ6POR)TmM9q=1X)I>5u&A8?J}9qbFTPE7a7{aN{4<~P`G_|K}%yowr@ez*}_Dcl?G9X>1nha6)a5gy3CrC@S1TMHH}1gld`2'
    '{y{PJ$>ty^5=wO5hu6|7a?`bx(4=`?xPmE(&Y1cpm)TX*^6M0@x#F0$lqb$*C%GFQF9hCm(u=7FTj!#lWmnbR&ot_oonQG!p`gZ('
    'AoHJam-waPw{dx{`~XLWi!mjRC=?2GQ`;9w;ja$;UR--huBN@UXgufUxtkieQ9!fjlHp^vi?zj$r`{qhb?Ab#6F2@#;!O&x~d~pe'
    'a!6Hvvlu?ff?Uky?SL+OXK=U%bed@xNt$}$^2H#zg9dBUD?Qe79Mf#+!=7N#5?}j;6`9d-vOh$MDF-'
    'g=rp`Q@Z7M^#D>{FHGcHgTjYVB?JOA3!Nj^(HSsLRWRfSN=4laE7;}XAh@Y6fGm}H|f#l0vk@+X{WRI3EUEFXG*8@C>x>B$t@Dpm'
    '5s0r=uWgky1_;&f3;I+*Cy?gf%U%Cu#boKHBV~gL>TCj8H4q;TqN87I)18QsWS<xTnAXpnc$-zS3eDj>JxAW)E#`9k*=R0$0oBT-'
    'U$9uo)++_2Fnb(2&pFCozOY0QVDYe}_F-Lp!8vbYIOk6USFJBk7ccb#1z)MP;pSb>`!jl|VBo>c9aq!>~anTVor@zcsU%@Z=`>>0'
    '@kG;)T;s3y^`7V4-8J8s26WjKLYZ|n^vfnVi#GZpVR^cZ&A{nqR$lPPuX)ro^FTM2AnIYL@U3ds}Ate|6effCU)T-'
    '}b6L(6U4f(R>@kD;u0ODN4YD!Ptl2Zb<<~SO@Cw>F@I~+Z-'
    'hF(4_KB_;@e$;h9j?E%J;&ePmj_mQnx7FCXb*EnAdmA@y<2~V1%a`{EGXk?>osGRj*o6ggT&Q)Ix~&o~-'
    'z`}lII!2gyXGwYU(glyue*2eQoYm5FTW<-'
    '$hZfiJb$x^hr0I7a&v!kd>wQxa|RlIr&X&~2=4`(tYyJH=KS#Ck!`^*R|^AMvu0xxYb#jOBl5lQxxk9h5grrw=XEg5f(ag%t`uxj'
    'HRAeA`CNI7&s+AhC6+==lsYo*Dfl4w7p#l-'
    'IX7gzZQGvAfiHFXk32#y=aJCACuGykp9kx`P~nvqEVo8}H6M<7m6*dBH%4}f!)4B=)>YQftU=X0<b04>iP`Q>eR?S6#J=xvlUs)@'
    'jvs$Qc+yi(Jso!TwBql^HC$`u_<b2CU6-ZLmi{tliP;OY<2RX)+!NyoK7uI}dvI7sdUO-'
    't<6L`ti7%7qxg+Kw^|FUmk97Wg>Hqfj+y5!t4gBbhH{KM6boT5Un!{zBYbAGO!$A(GKfEIB(_@d`;n*s<8u(hQ$;Gdu4hh_Mr(=z'
    'o`%it`{w6kb;so6Ba7><3Pcv}-cpTUMOkyAnew6$dPc?Nk#zG1{TyQ1VwK1qY;IjoUe!Rg;O24y$#hH(i&+?o-'
    '1^Y6vXE631JHVq4#&0~K-'
    '#mL3?C4$94i=qzBk?2ZxB9p{bKONY@?}`_SX(nMR<Uzrm;CGEQLOo4ckSAqoWp&xV{T%@m`mJi_Cd#wAL~~ulYG09T^S92*_HU4u'
    'Cw63Cu&Tx!I6x&5r-'
    '<@d9r!Wy{6m;3C=rm6W~)cubuHYK5NVl4#v0MdPm%<V7}B57QFYIN8(2>H8lptkAC*Ep9w#TF(`h7j$aLaRAWcRkBlMJYf?Roe`F'
    '6?#lO*UbG`llfFJ$!U;p*cAO7%%>bXH)RjIWv^;^Vdj32pg<Y4%b>ly~)N7g&%nOkP{=lt1}wfswPRrX`wfFHH~LikbF74V~uf%p'
    ';rE^BM?N5rkt<dNdXVj~?#t?{FhGqqR8j9)cz`N8lba|k3SrQ!qjH(9rmPxk*3e$=`GenbsdSK>IrkJuA4cPdV-#vi;Aev~>T-'
    '`(7uSAidO+Fxbvp>wV~uJNORG5PO+AGHm@k6KrWAGHm@k6Pb^A30WPJ705yT@8N3y6|oBBjox&j30GeC4QuuFAr+s5<hCY0)Eu>J'
    '@BKZ-uVA>{HSB*%=vAJAGKWuKWZBUKkE8Fh99*C!H+urkK;#OSBW2W4uT(b{vW`PI=%yb)cPLyQP)-'
    'CN1gu*_)+Kgz>l=Y{0{h0*C6;&*8u#e>o15Ob^ZnMqt-zDsBqMEH~0~+eFJ{f`nLGdkt2sYQ-'
    '5mwsOx_bKf2~y;76U`gdc$!Ay52mbBJ69KWZ&ryrRYN%J|Wf!jGPOQuq<|M?<Pu^<N4<YF!0>)Hwh@>il!#N5qE`Kccp)^$qxu>c'
    'Sp->{w^PkDet?aLpjS63sQLTG4NTAE|!poA4v-4D-'
    'k}NHu=M{wr*dYN(L!{{((i`ow>K{0P0Ho`(Ji_QzNs!5h8@e$+7#Ke7$Vy=lniK8*zn=4a2S%i>3^tHY08yT<xw{OFH={LA7;_D|'
    '_sWBlmtw+jbMjUR>1d~f`yuix5A=^pi4bLY;9dAz);J^Hrz(XIwR+Oy|U|K|^X__N|iomYb&QG4{}o0r9p<eywEeuNy&<!Vf*)O7'
    '#3@uS1xM?6BTi5zp`4%8cc`DGt|^u-'
    'sy6@K*g+ZR;JVD36_AGqiWestRSQP&mlqs|IH>NI`?7wYNLuTtybzU!fn|0({bix)q<8vLlU#*c_IAiphJHn$Q#YJCg*NIvQy_)*'
    'tj_|e|IhvbKqI+wkw8v;85FWR<kx8irmgqkAaC7eU?Q8t84?P<Z)K6~~;<43LUf*(=CRq!{}%czFSHA&QOeOvs<HC)&;#<FE=Ti<'
    '{mwFbeDx~>*KD#v50<#NpzpK;9$p8-<>s{=d87*i8_q9*TZ@T2|vjUOEi{Zrqen6Garj(_&-uNw@h#*adV-x@!vIVhJcTl!7-'
    'QP+3Ck2(k9N2Qigv3$keUDLs_)SdO=M@4@%=Y<`W`E2~?aPsCDKiVzqs6T%6d?&S*@4N$kbY8eo!H(V(cGQO<oeNz&+x1=Xqx9_t'
    '!;iYYBYu=MM*Z<4u(whdsv1mT6_zu6e&2u}b=LTiYw*xp_%)dOr3Uj6;V0b3*I$1t>$cv_Ia=dKuU##E)G+`*YW*4Uqt46VN1cP='
    'N0uLtxkk&|qtvxMF$jM2YJ+ovAAuvCKK;ri_))3h>cfu;58k`VF#x-'
    ')YNwlhT7@5}FG={v;6_9L?ce^5(f%L*@gMS;;XMFPy6L8y*e3}Kacq#mT7pc?lYx)p$M_z^1B^9!7-'
    'y>2DEGiH9#!|#AYS0SPe#Up<OevGP!C=MgId47@F>G!3-'
    '1d#3G|xbeix3^9XVGHP>+`Ub$b*`z*d&Hf_TOF4!=P>8h#?xg%G=;=lTsd+|Yi@Ew{8&yY=HA|G53uTW{6=f;}ha!#p)V5Z7AUO2'
    '<-'
    'Jzw7!U*KF}w*F|^?tV!~3A=8wd^04vEjPd#RvInfVEjT~!C;wrtMr;uLt#Qt6<Hn7Rz0Fj`@924S+ifF}2f8MGWo}>_i~O2;TiI^'
    'bAM?VL`1E1DXPLrdN6c{6tocL#=5PLH=->bS--|zyeItAkwr#{LlYgkuk%9P|<I|QUKB)V-'
    ')jeHnj^w(2tL9EjKR~@(S*O^;Vt3I$bUJ%67=L5$EqsgmpTxctW99LE_swXVI(3TT&hRJRfB!uEJ@q|fK4UxS_hH+^KsWKFSc9;k'
    '^p^@5tCp*9AIs0cXA4=)Q9O}#G~*VsXPhVZmi;e}+3VN%+dz(|n)}YU1~$T+Vl{8K`Ps0&$-nB{FXc|-'
    'V}{(><0!^VtR5~R9)q#r2fzWszM42Qufv(io}Bj>>@kT)Po6wU9E#w-@cn_EfBNa?;!uRAuJqh{D|0}e68?q`W^PVDyN=%B=c1b-'
    'KVtjszxvfJ?bly_lh$0~YuGa8O~sw4HD#dA8GCcRVDd#b{-'
    '^hX<}NZ%R>u0JpNY9O7zp!@m@@t)ddGlUrsneVxD217;#e8WYOs;1Qzr|5yX!9S%}E{fftx;kmhd;`FL`bFme@gjnOK+U1J^-'
    'MB=93R07s1)tM3x04%t%srP`!hZn<6f8*|2doXExdkb(B8UIUDUyYG|tj_iBP2Z-'
    '#F=T~dLu{dJ?tij05^;>W@kypSqgTIA6)*Qu$`X;`~!8s^r>bnJhyI=SlIOGjC+|u^*pWn~{?;Lv<>g1hY#9AJEK;ds-ZMWY(O1K'
    '-}14Ckffr7sk{=~_`kE*q_nTvI<hV6fizgeElJIAb%mwRZsp96WwAAkI@;-&C0fz3HaQP)#vUk}+g?{UbzCdYs{BS&Iq;VUQ(WS-'
    'M+8by{1WdrH0b<aK1gumfShHt}OM)nTBo*WwX&*3MrE(m`Eb3;yGZOGEk8RQ>?UiOn)jlB)z+cmaiF015QYjn;1*j=BRvc04iJ3L'
    '6lq_KV2Pvb7m{Xn0Y&tUr5Cq#CbcrW`%atpvRkt6nxk#oJnJfG%3EkoEP9Eq~`3m2}CPYM4dF%NPuz}x6q#^)HUt=W@HvV*r0PD*'
    'r{US{wqg5}+J-`s|Gvc}+yBN=}i$m?m{Lk0t54xZoWY4*$`UVOQJ_L4bqVA}#>-'
    '@Z5KEB!p+W#Y&@58c)JhAfGlp{vG@h|S{j8^65oK5XFZklP&WUdZ}>VMZD60E?4vh%Yy9-'
    'V)h3;t$Tb1T&d7ZB~PEB3ool9SOe!M;ksAdWGDKRo0_mmL)F6+<W!aR~p<Gn`S)4c|hn8zsX(?4mvm}<9+pya%`NqXN|wn-<-'
    'H5vP0L%{Q~<m?=09H>s<Pp%Eh9W2J@ZxE*RWE{H^d&&WdXWb6O<)4SW|qJ7kulg&dF-'
    '+!ydVkQYoY2kQyGA@K>0g)4u*FgpC1j1x7SYv%hix3<UW(=Teg{POA031Z`Lc)SwVc8K0I4fdA5q5h$K4?D<jW`9^=9bj=+h|M$C'
    'B`f^nn2X3#YZ~_!e+s{4?AWo2ftMWEMNQtn^J4qPJn?ZA&dtKR2@mIt8FRx1%xuk>vxvBmu%q5y@ruMecp~gk;hcc~<*Tn$do-'
    'l4hUV*#&$+H=pM5Fr<w?aD>wezG-}>bFl6Widm*AX^qwGfLIQBK}^HOo#Grto%5qBc;bI<Vi-+y0zAMyiB`0~py!PhRai-Ywzg8K'
    '~I&vpX4K+YfY7n};*4g88Y$GCChI^foebz2;k*hKd5><L0QGnOsPk-p%u{*xmn9zyjD`tZXKF4r^2=YkKbxE_3-'
    'rKi%aez=?E$2_v%M{Z%+7vi7qiuo`vbD1W`+BgnBpZnbKm4j<A`2DPN$a(*2ocj@7KQSEE1$Y7R1*!1~y&Upw`bW8^3^w$_g?E~m'
    'CpZ+pi9G<%ppNL<Vj{&h|CfCJQ>Tat9fxO3ykpz9_bPTw|C|jQ9&GsktbgWD+_Y(93;cB4xO>}fyzzGJA>l-'
    'ZKL9&CV@8<^#a2D&{ZrW0#gZx980bapZNhdaFHW^dU`reehI@Yp`-k{ki+iwYRX5l~+)G_Qd}%{md-'
    'P`>%{>4=BL4xqm7IsziZ1#`!n;Th%8a$h$1;y0x?%prs-H!td&;s81<zTv>cN-'
    '`v*S9aci=y9gd=&@ti{RYyF4+WZrN?HqbXDFjX5+~aw;*IwUX<~l`C4wYZvFy9gkPG${M=3#ei39@#00|0bI6hX%}38#L&;4J$JQ'
    'zxGpO%YS}*e=);(^&q<H)Cs^aCAqbxbo2xm_x`p3>pN~FaznLG#oRJTEH1OD1qx$tPV;Bbpe=GgopVEGA%^G^F(93(bdVZ{5PhJE'
    'yxT~9dlEN{{IzLy(<;#g5ZBRW+Vn?mSmE!*kh6L9gy>zy3->;Z;tb-c#-FfiAt-?9z+e1D#wMKo|TYvd{{q-L@-'
    '+lM}xSlt}FGQXxcANd~g$wV?UncHCzWv6Hy|HeP)2tqc>M>~UTx>S70zU@Rqz@YFA35aY=V33g$;q+a<V9va)g|~_=@tE?^RpE<W'
    'i2Gm2T$UvRRv?iSDHV+<bgTgq~;9n<G+1Sc_+vYPAK;2#N5~i5VtP;X?=q@5`Grf%yH}1UBcs%*AC9KE_@Gs5PXsFlUwwc4qvSm^'
    'QIquG<WVId}jR*@#?3aenEXck%M!{n2+F+$bj_*J#;?=`)&9U)Q8Ydm!2`y(7|a8#~1am9>$TF`>d_xzQC_UY=ODGY14Z3#6T{{1'
    'i!S%V<)j5;hFT?jdePFt(EdS7cN{b-rIHSwpJLA<S1E{dab?zUc|`yqF8%&Nsi_h-nI>YZM%G4`@P1Ch&T0(!t=;~5=SZgiuAqg?'
    'aDYwvwvql$zB58q^}?HbNs%JE3qCQJV-'
    'o+SPHSb$JM7b{AKkddf|l^)x!}x;T$L8`S`2UZgqDri|1=3H+0DHA74+=N#wUAeBxDcO>j^4##*v7&Y8Vp9|mXs<(j9jaJW5|cw5'
    '2Tz-*0k6g=aY>bgn|LSGI&F=pgw4n>aU%?3w}y_x!hBB#>J@p13<n;Zgk4f}__F?U(h9M3O2ZEp+bDOmFH%weVP-'
    'tjme&i|P3x3Oc#kUQJdL-*lt4@h>%%5?w**V@$#`aW`h!3g0BhQGV?MtW4((&LYlOJ4dI5l?cjDDx-QGGpHl#sj7S7ayF9?ECo~a'
    'xb{s!<zRQS8nWp`}>wSUti5);p*>IPE+i~B|FvwIMdzBCuP>J4@?f`j{cim^sE6=j~dp1d+)uU8h8!-6ynmvSlP>O-'
    'OAV`eAWDk%ni>$=G(q~N9AAB6A3$T<j7I+(Gq_sJ#+CjpKmz)%=uSiMy?$+zo_vvYOVMVGBK`J@Zv}Hy@Dw{rFebv+bP~xYPgO`Z'
    '#YNSV2~q5EC^l0Z!CEmZ#J@Xp0aaDnbUC%9ptu<2gE*-'
    'eo+j3IoCe(9(|ti<=H=FZ&2~=vIoEy^5<F8owrtU6t*;d=g~p;BQSnsT*Ea-tn(bJ{#ANj4}6F0J*RtV+-M-)#D9Z9IM=NHZh37-'
    'zP`J`tvR9xw#m#Z);QZ$^dx)qDfYlVEcQC>!-'
    'o%VzyA8`!QC{jyY4z2!QP0!5krr;tNjJ%ofw>Z6nfvGJa2QoCm!1Lj;e7tj&&^7a?Bbo;cv-LeTnRhL0i78XYNN=bD#Nro@YOHeV'
    '^aN_htT+{&l+>88Rx&O)_(z<*-xKkr01TEfPLk9NTZZ?Y5!6{N*o){>#7o%g}%Nr+*sy&;R_-'
    '?Kj<Yllom!LxAi;?}SG>kBIe&cnHtka|?Mom&Wm|T5ffpE&E4xj*@xG_$}lI#>{Wl_$99se*wQ_xZkMbyy=Un4uafg;(zztGcm4v'
    'blZdp<6Go)VS~emRgM=vG*~+LTB$wS)#R73CWO5Z=1CnFasBLnfo`g<DfSW6y-'
    '9Z9Z(uLvL9)JbpEy6R$J~6@71z)hTg;eh)9=lC=DtbRHP_2I*W7rgYquOf1&^_wQ5V8<j>rsbjx~(<0QQ65%RC*)FMbCeL*X9<L%'
    'JvS>vw|F#&vI0T<E2jUe^B|I&`=n_K%)<*pDaIgXicXpWVHCAN@Yn!z@Po&wlo^_Rv4(u=ZNc?K5{hu{_5Cef=KH<J1@3OUn#j+<'
    'EEv_4ooc&wjmEbp9M`9)2q$WTopLGiHo(oXsm#Y6538HE-'
    ';l@u#r8yiVLD<5$9#z<(!CrjPi{7V)Wz7e9`@$Or1H`pPTRU%%YcwU_mz)M0{IqI1Oe_wPTXwHn(;Us?ArqyN^8H{RL;J7rFgmw}'
    'D2-Ni<Lt-'
    '9{RI#k!b)pe=vPm#HYUhBodTDVzD4`=7`BTwX*J*2cZXO0qAX70J)8%Jto814gC*BpU`@E&n|zt7`R`!OkGd>{26@|USyB{zxqp7'
    'Z%wm%-iG!#LK2?@zqnacAlt@W+|MAxG7L(f@7Ouo32#Y}LFxmWi=$=N))1)@wn{vq+vlI)-'
    'nFyax1w(B2XKLqCz3_vm21)S!ZCkTc@C%NpZw&DOwix!z@^r`~kc4vic+Cg$%g?LYtd4ei%n`*ZRzltWqS(2q2Ehxj_-XM(*^9|('
    '5YZX6SNf-8X`-E+^>c539}alhVM#yIN!cy<1S@i)tk*NCrs-^2bp_lJ$&Uggd=_|d1IeyToPu7yK>@tf-'
    'Z<hnuTA~MK4rbZvpH*g}JU#YjA<$K?K3*vjTWbeUs!GFVNg(qCTAU-9&FC6G+&z_IH@M+~1ATuyGYTdGiu-%v(SZ2zxAAh2K$-'
    '!hfpgvQ$1oC1|X3q`9oZV-T@4<0J{Z{O?FWb)^UzB^1_EhIU-XZpcTrl_1Wgtg#5|EwcgG_6jxURpXej40}-dl`PN4-'
    '${keJJ=DW5lQvG#VX4dex}=OjMI=fT^u?y_yfh`V(JyF_-'
    '}3;OU4#@|_En03yEZK3O=kzXCV=7>#WT|fr(?je>&O#jT8GxXaMZUlZ*<<6_eJ(#9rm~}o3&+(bE54-'
    'YPsE0td`1e_>MgQG?{qy?taIOY*=)^B$%?zIhU+ZDTHRx&PzHi{0p{Lp#_w;NKCO3NYIO3k{mBqypx~b0+7hxaG`pVu9436Q)#xY'
    '&fnmhvy?>h40y6g|v_A%FE#pme(kE}x;s!zEL#?TMbWGzO&o!4$(6B~;UlYX@F6xoZL`wux9`z`j5{Htl9GgCCijF}X&nBFmY@_p'
    'Ky7943YGHESbxLmO@_JXX{&ph*T*zf-y^1I*t$?^ZNOYdfUg#Hrv>HC}Y!oIEfoGM<Y2D{8&WKHcL@f-'
    'J1<#Wi?u~=lw`hbqQCn0i#CvK3n<q|oDeo8NiVPY$>6PzD=ozg#Pg>X207zX$e{th_`ciwqt2l-'
    'j#uuYjVRlShVSz^q^=XzKe66eZqW3!1dyU)#F=M#Hk#Y^q~=Nj7&tIS%*Ca-'
    '{V=CNg#ehJ^h7U3&4vf&u^PwNT4LyQ(&3v7XSu6x3{{*ZlD%)!v*Q;PL|gI@N#maqZBEx?V@SNam-'
    '58D=DUpUtfKm1U=dA<ui^3_*gc2YC*!VAv}Ln6k--sR-'
    'U6PjBkH}udYwQsgx=oIo!y;E)(xruOtutwr%gb%Czr1zohCyCQA{~def`_!8t&r(l#0UjFq90^~XIB^14lj@JUyH|Gg_HGkr=Gn8'
    'ai`W12&wulmz>oUjNTKK9SHCNLWG}-#Kv%(^T{G_5822y2KaTyyCH>2od)OQ7Klna*CFIu;|HDtkC!>zO<k-'
    'n?RWB{#H(5WZHItme>C;OsU&(RVBRq*Y2kyr2f;BB%xIkP`^qY!fi$OitiWSS_{MQhhL-)Uzoc{EuKXM<0A3gKT)7txD)7dLv3-'
    '~{J*s<Or7h*^$AFX|vBVe1Z{8#pt^b9lp=K42u204Q_vbNzLATM%u*fZI$MGmfI;B$^)kvE0Eiw_Kb2}ZYI!7|m5md8tlGc8=WOq'
    'ht{{?0jGxpJLqTsCajrrJ{QBXE9tz<l=EmzTwle*4?sb<zjPxDoY8aN2<%z4OldA%oZD?@>2H&%Cv3`M=HJeCnfC@SGm4dH7P9D}'
    '{W-H^BT!o)G1E6C(({k*#w6f#)y20&_R_2-'
    ';IQKQa3s>F9ox=48wKo%G43hfdLdrPM2fF~L7${4IN+Hn@dr=8Y#2ODcPLaj~ezh};xnBjoGRBQX0#^IqufvKGDtxl-'
    'i(;ETjjSklay^W)qX$k%fX6m>nw4@?!Ax$eyv9C#aXRPZ;}7IUk|T+m$3IxN}8=btAB^pwVvPd-'
    's`^_INs+?y$<jJ@)}+WD|sdhFW4`Sa&CGDUu_gF|*H$EHTfeOcVY%W@<3p8ScKpS(k|<9+t>?hnPWyL*jl!g$Ovanj~k4KOU#c5U'
    'CjTbKpdB0a|NBk&>2`@@`N4az)5JtiJa4hrjG>Lj@w!jO(0C3l+`csYV2fhU!`_QK~7LotSoYi2F#n(Xt|qsR0~+PHC3$Ab^Tlh`'
    'dE6ijo;k`;>Cx}PWd!nKxt=uvU?f&YR{6xkif-fF6U)8~jMfw>jjqTqA*!i77r^hHCq*6Eu2kH=te#8-'
    '&zk@E~+CHR8lha9svj`|DI7m@rE<|h6}mDjDf2=d##`w`XRu$L};(Z?(7;gs%A=%Hen#N?1&A9v?!=~KawwyP$O0k2-'
    '^PrO#Wo#)P7B-wG_-CHbcZ8G+@v*|@%W0&qhWh{=z;2X&Ws3WfvZvu<t_lP&~+ocC`iNiCv2Ykl(CN^;S@}9U)yP6)@jv+a|=6>#'
    'AN%&&MK^Tc;HuYidd5heLiShi=M^BPtL@tKbUt)2r7kwPnOJvKy!X1C)8n9u;56}s&j~K7(Qu&Y4U+h$ai`CqJrAOAIiUGSu&^RX'
    'hgX93@*kGP~&N6ZxjO}SThli^?sNUqY+SSA^9nU1MIAa<OPR=p0%YOOrF&aD<eIhT6b+pv=iX+av7K(eA?}vS+*IwRtPvfl7XzGK'
    '_gTQ)E-VMG2kBKij-e}AMpNjYRF2Cc)9NBZ^X!JgLb)18$ecRNjQ`<+48rA-*U;V26jyvvPD0dnxf@@)o?W@}>13h)mZezx-'
    ')g(tX=DfJ-N<ME-lUI>LID_#T_U4wG`(h_IO~xeebzZjoJLHD%!e{v&=f^c7E9WdD7suk+x8k>BXB^{63`4#*@0Xgoa&75j^&95?'
    '^?gQu+4oiVH)C8nA7TvLzj6+}jjzx7l+o+BOEb{RdZayV<k-I!e66oZYbsbK>jJui9FQmHO3e@FW&DzXT+!Rim6xo|(U-'
    'h;4F*>a=80plHK&{FPb?#@&)88tkSXVDP8(!X)vM@rehWVV-5_7Dw|8@;bL-<jkm*M8kD4#h*nj=J*yw$V7hsEuUP?dX-fhJ0tIt'
    'EoraknWT0+IwvQM(GH}dq7XG3}0K6lQK!F3{U=fyExx0HL)X20z|A$5Ga#xxz9wJg!e!RiBz^%~nXcF8by$8Qvz?vWPxqD7WF#Iv'
    'w{`%d*y+_{tgC^%86S9bmKu4e4mLC<>d57u+n6oPGPJr{oYi(mXgwU=;F{@@2c0IO>F2&rcwzY*Qf*k4nx#~@D-'
    'c^Wgx`~=k{pl3DrUELqoqwZto+(XNo@4J4&_yYS%d;$9#weMjcmG`%9-6T7?aN)|B+w;SAt&ZO~n!KH^tLDCe?cl@hZE~ZE-uJ2}'
    'Bll?6uHKN{8u#p0Kh?5ctZsVeQMXF%C36&AGWO3t(Rpn4t3CfLN6W@o5XX!aHhPsjrk(Z?@DHkE6W?=vCwP);Fe^?~-'
    '7Bvt<TddBS@$g*llnR8zlo!c8#k7iDfma*%{LFnXN3PjwS%nj^s_y1V2|V8&01!=QDgRLa}{@Vjda+tq5t}?|H>fOpd(`^9ciPbP'
    's~Ht2iACqF%k2vWsj}~gG=tGA@<p8UKM0$u8WkR<dA)uu?t!k$PdRBa2<JVvbC%gSvx3Of$ipcSVyqI%a$#V_wS8$ZiZsd_uh+6t'
    'm~rYAMVcc=c$o;O}^5hL;IVY2g{F~r$-(+*gA6LP~1b-'
    'wjE8a#Fj0a=&K#SIVtYX7}*8O+;N%YXIIXF>!k<Etmd7l@ypEn8j?BT{r36fh|}|(J-1`oe9v{5$s@{Iq_v)SMe-'
    '#|mf)KBPaKUY5&yv#;5l&(*LRi2)X>d}IW@OM?P`(Te~SAQ8NT`EuS1Tn#(g_Q57wB!^w2sWo49e~=2%BJtIsU9kG#7*d-'
    'jJ6*SFt!=a}{pBSweqyWKe$w!2Ln-m!S+stl|fuX{4G=RucBzv~w}GdE6kM}u*NQ40s&fsSVUM>$035bG6jLDn_n8py_Y5wc+z-'
    '!LA>XX@ImQa?y-*G$#>fuVr`4Ie%lOjo)G7QAQA!{X0oZ*$@VITj~~?S~IJtew31n{FE3cKhvj!k-'
    'wry&>+|tahGHnlud#&wluku{iT2R=92>JIk-;J<S?a4ffs173&-XaNo=HDET9Nc8ZOod&GCB-'
    '@xC+KPLYM9ka|B$Yvm4tY35OYK<RJ{{|jOy&tudx86E}I;8AT{D}6^>|dzABu6^-'
    'F<~ojZ~Mtlu50_{FK^Pg>89J2J3nR0{kj)mn(%m1$650dy9Um4w$3$R@EP;6p>xQGxP9H<lE>he$Q>I%4FFtL*g|SCD;*rDlZyW{'
    '7x2T;Lt>58UE)jOTj396T(QA}kz3XtNneq1;>Piq8p(S@_a;)S(stWzqri{Cm)IV1I~3;zN80k(2e0W`yLOYfiP(SgKK(M_Ir_sN'
    'np%fgr(O&jvMm00p779#6Q?ygSJx5Nyr;DsEx&>IrE9==j%{=8zVAiuF~NDs;kf21unst96(4dO61~Sxvwo201isEb2<!-'
    'M8v9$=OmgnRFKfe}7%^gGd}gxvFW`9t4+J}U{`nU=OU@A-'
    'xTia>P+LadDB@e%(_m|DhvAOPJUP_``N$YpqhHsT);MM#56P2_AA+p;UGlG4zq8&?Ioer2t-'
    'RRFaP55~b_8a0@#1^ZdGsIu1^bO}mYAvPnqGhXwa!mI`FO~;=Vbd@IL-'
    '6VKc{*l>QTTKh;4#3tX{psIabYFt@Byx`h}F4a&2FF>2zXruj<^0MPU2WH*9bxug_cuKA-'
    ')TO5RO<D_m&&K69UQ#@G4mvroB(za(x{;iP|(PXI>78fiS7BYR2rK&Eb^w|9&D!M%I;z<(M(j`9L7!7!cUOZ^~gB!hJUxt%``NAc'
    '-c%l8r&O#Jc%y$63O^P1QW^}4P}=Q*+~ea2O1EpB4w-'
    'Q>xWnnBG{KBk@vjydL*c;vqR`oF(x?UDQ@;_$?b!GTK8kL|jD_{7v|p||Xt%(>1yBDQL7Txt}K9(_c)@4OEO;J$qiT~a@2UX0vpg'
    'k4iDXUO3KoE2K%XU|^LHf-2vY6-iz5AG98?k74;9+r7}-'
    'S+`qCGO3=4w)*(Q~J~|7Dp*~(xOExV%=Q@#?*?VFrJkwg;n5R#5(=SH*rv^W;1N39#iWH1`qcpvIB!<PfUFyF%IvWT`z8~KIb`>+'
    '+%zVco3h>-1aAkjSJt3^J{n<SOc7!=Y7|K0|#R*+LgH<s(+Cmz<y}Lgeh9v&=>p;;x73Ah4Xf4!-'
    'L9RkUb!KFZML#n3tO8WvZJ?F5G@KN?;+xjm!lEe_PhWfPbj&2;MRBrqG97yLKwS0KbQI1)tg@YgpwI;e&&<vPVGg9Fy@JMULniu?'
    'KvI4I3V0kLTX?>eo=X@^?Gd)zn@ZdqelgsiZ#?*zCA*Q^Fq_5q`vY<&YpVxVWcJpC4=Z0&+Y<U*<JDp7dV9Z@A~4i5=6XO%>)#9p'
    '?iNP;Yp@uwS@6slQ==PaM+t92gIB0#l;rL8%WadELkpxf1UtzlYj!@_FXYCGTg7YCid&<;$0<51q$~6@@o+<w|%mSLnEERX2P8_&'
    '+$H7pZ<RUJH2<+uEeu^39v6J$gtSTW8O{rCtq(4?ot-iPftgB%erjt*XD&Isg{Md}K}AwhgYQ2Rh*4pEL<ycBb&#MT?ko#PHz(B;'
    'HCKnErWll(!fo<TX34X^Hf#r)RA&CXV1t1#c=`mEf8M1K!x+mvs*ld@}NoiO-v7$uXy`TYFn2j!Jx)zW3`i)~(}SJebed<{-'
    'YlUIXsXjT<+`d|)oGj(dgOI~H@699wwfPKMojYsh==eGvXX80H7s|2_BIi^8mkPj`3s&p$vHlk>ERt$=49I`nYHGvSvc7oHev={-'
    'oT;PT}?n%~sNgOQW(x@5^p*|N23H}{L#_VjEXpldr7=Ow0Q+_xTZ+fe_89RjB_#$mp%(lcgn!wbgm!Hvjo!`Ilq25zHXU$tse<}>'
    'eBUhjbe$70>1mJlxRv#~~!YjPoE_EE_1-'
    'FW=EdLNxTcSboeh5z(S$n2RW&(FLru9L@h@*aC%$B3xEWc|(<ea4&DHvFf{m#=DYUfZ>S_RYMgrDkqta%t{t;=QG3&O=om{9fU}U'
    '~ynT$gcG1?bAm-=h_YAQn0Jd;<zW5nb^DQ2f>c`Kk}WqC*YXw;RS969>r_a<PqPZw$-'
    '>L>mWz(xx(LQ_LqqZX$`=)KsFqS;fK8195br$qc+Fw-'
    'S>obfjAkl9*#UWJ^^+#5XT@UYs>>Y!<a^5J^Bsq6|eJKoKqhzzp@#;&gb*Kw$W1u%m!SEK@5UDAL|^S<+u1vb1*wDN?gy_3ZLVDz'
    '$g-'
    'vXn2~_cg|SZGQCF4NgZc1ze?g<&Hf$PaXw%m$jmrM;zvy_80%Z&7``s!a*`jhUSel`^{~R0oBKw5w63=+SXt>0;*s*xy^Ot^cns-'
    '<b?vp+Dy|tv)lz}O;cK$?bB+9#v90`F^EEX0Y~ZNxFW1MB>*o9TL5YD$->d`12#sGdh>5rlp|8Vzpsfd<+h8HwTV!K-'
    'x=zHsF0yW`WiCd`x5n-2VVux<!nqOaBfp9LFGpgBj-'
    '?`Ve#`jCKs>L;GA&mR*Vi#eJf|#QWXLei#^5vfE&QitnEIu8i$7&uOZhbVm-umqx$n4k^L-'
    '*4$Hg*U*zgHD_ZM8lSf+CcUBfomaD2V^X&YRZXMb3~lU(2Wyk%0~lY(vZVNb@Z>i=<_V(Ml;J&kK^<Nmo0g;=j^RT##5-'
    '7A7Q$bY&Pueyi27sh>)E48Uft7EP;UgTjcu6_=-m-+1dhU*0_r@9u-'
    '_lxiG92|+k<2uf6tkb_y|Gwo|W2eX(nV~1>2zr*brhUYS5sabNUw{43AOHBr;-'
    'dV?Pkur@mtt<V9d*AtuhZ0|`5OJddGDLrF3Zn)=RUc{@9>ozcW_MG^$f_+u{84N&{0OsA)0f)EAdpF69XGgzX+~7ZNFlR$Z^Mxoy'
    '~k;7%R5E)-|!b4kpfA!{)DDyH2u8+bg-'
    '<aKjD4FMs~?p9=#f##P%z<Cd=Rb3ETMe#f=k%g6E6iWgpwv*uEHi2Rm&mwCUPa??4xH=5(MWj}vHy5>1$Y>*fsF-'
    'PLIu?JQExa<=V^N1Mi$hN!g8VyDXe^+y!<TLYs2M+8{-QL|`%N~37Aj@sizjf=@!ut@i*_eDRrT-vxt3UnePn9RaJ+mEUUE)5}9H'
    '=!uQV(NDu77tAa%zo;(UV6{9vv|XVp`^z&wZnGkl!%=hFzui1-'
    '8xek@XEb%le=7T#{v+oAeCZ6#6fJ%W>%0v**V8g5NbK&huF3yYIdy?C7PJkmJelE%ysI-'
    '@6wXvbT9i_z{nH@7De+<UkyYeyQvocCpWD8#{JFtm~sBFV2boX3jhJ*Ya}>bS<m8-'
    'ov)cHJ8SZklmMGemNNCL2bO^)##|}JE~e%`6=K*=n!_e@JN<ALSso_9_C}f*E8nEd-w?CjFs9s@z-'
    '@d_uR{!pMCaa=X>vc6n^hT?J<Zcz4FT0xSl6fLkKqlHH7%$>(;T~-r50w5OJX;OS;1r?v1&-'
    'gBU>AyfN*gMvYT{3UUZ+%UqvqyW=|Nfi*IYN86TJpIpm8jv+eezEOk4nv$1BaV6{<evjAr<fv#cA^T63pPw5?a?NUgZ1Y~#4-'
    'zwiw{PCO#p3NFZ_T}1*>{kO0G>pi9QD2T-'
    'g_T4gdJnY7S7a(6Q`(e7j^q^K93nQv7H*i(WA$@F13~ZLxbr$PotKbaX8P{tb2A3yna0|-9w2Uj^t`ysc%&1DW4+-'
    'MNCyb9GDTgXXv1F=R7C92Qud7QP*+Jm@!@7z2}}8;77tEuf6scZ9o0#^&NNKIYHRbx^-'
    'I`{<;GPjwq+_*s+uBn~C*x!gutiKQ;JK>%@sus=-8d6DCY)kNZ-ub1mmFxXx`b%-ps3mR-$#ihbiqjy3D5?+2VJ#O>j-7;H{kjv-'
    '^!!ep(x^pQOm>pxt?_{U&F_LZ5>;6=vSnZLYN@S|JXh7Z5JZRE&N4c-*8Rc;RWQT9KH^H+>lao5Y#hk(O@zte-txTSbJ$xlz;wx6'
    '%%JhPfR-2DfQza=MKQ`5zqH3wtjZ_XVNmOyMW<*0m)E9m1T^)2A-Uw)|=vhPci-'
    '{pQz_$bLgsTeK)hdsV<;hk?&gCu!<_SvW4J8|w?;Gfexrv8u`Sobo7KaE;MuhaH<EKmEY_`&ASuJf--uaQ%Y-'
    'FFTVwlMP}wI4!$?r-'
    'Zo2XbWH;J#C1MJ?7KHuAf2(tXR?qp!6lgM)D&@N?l2F^4622h>F*t{@K36)V=L7L)vcW0lCq`C@g>nDY?a(>HkvTtnFSz#duSr2Q'
    'DbjlL#6(9dVKerDdF{*!gwI5U1CcJtFu{|lbP?<~{wom3~tJmH>WpV(8dKPPq+_A+emGGPFY6BW#s9M5BM9rO#?n|x=zTBC`f9Xx'
    'oX!Pktr)%`7ym-'
    '&dzjmkNI^&zL^Difz{@{NmYjMuS=#`bs}Tj~1rcwP8F<^;QEn>aPFW7JMk_eK5Ip+oQsptmQ6eEjie1LX7dpqz+<4f>mb$HzVDaR'
    '0sBQ+XfQtex2-Rem}3Uf^(t4;P>0vBw@2w;J_?^s3>SYVK2GaOT59UicVb)v-Rv-'
    '=T((8d2&ah^Z3q&K@kfcg#<|1BS_WkSX&u>sH}JRh*7%aIebDp=xsbiRr9fT`)NCBk+zjYc`0xj$R%YE_@h%T;W!I@x>REf3#%D1'
    '6ptR9Y*=hxssLfBlhyxO6R9LPuLhZHmK$dcfKrrOfuK8seyr8*u9{Q!*Q*dS1O;ZtjD{v@61MOi^NAWYSakrji?dCPJr7OrzzOl%'
    'J2{9qu!(Y75A};k8IsaFLB~yi&O)#c=3E;KZP@jnEx92@z~GsVPl?c6kY>P;5xb)Gv<Z<&gz&nX=2!@Nvc(xJ$t73LE-'
    'C~H*bz`Eif>02ROfSZcF2wx;x-6bsPmf%-'
    'rOrM=5&<`k(IFwKMt7gad~>b}=tn^cLyqS>3Ph9@}6UvsWSyZ|vCdZFk%;vTfL~+ruXt6MpHmm~(K2Oc&2Q$GLOo2|rq~q8oX{-'
    'r#=m){GkmkH)0XDb}h*Jl2>z8J-sM&=-cUHYcuizOD;gY3*9#!5g$^+OlPv_D{sydwX{(ADJU@d2pxD%?>ymdwN!hM-'
    '=_*?p~FB=Xx5Ps;@R`jrRZi2V>p3^}6TeWMKE4`&i=9id)9KJ<47$bp93UwBU>k8(BC>moHz@>_6GV*ZH^T-'
    'uCTV<M%hjeO)X+e(F?m5f{e1TPR+6My%r@gHoeKj~05<PoF+VgEhYJdw0iiRh%brkO$*>HtJ|>Bx{&D$ZZF2u6swA>x((?@WTgmb'
    'l!cb57`1Yi!eN6FZD2P)!n_Wc|Y;Kc)Zc`MLtLs>&e=3YG^Ko-'
    'K5vsNAdg|ezo$+nG?&GuhIOiMwfFzOU&tb>`NXMUy(5&{@XYZuep|lUd{ML@WeCRZ`ZOZ*HAE|8uO)YrSSV~%|2e+8$KoUj+}YN>'
    'mGV&j|SK3*y)xn5AnT@QtP6cg64Q>y+)B=;SSv<?$zD9OHB$o18&Pc%Ds5sdh1Q)UcCPL8{!+JUx*){IdhKuOJaXbZv#f{%aa?1?'
    'M?2#4&(ILS^F#O{qSX}FNF7)Tx4SV?6s0-'
    'Nti!Ad1W6IH$u0FN1Ch5>o9iT+~UTc_)XXL)WevL2k~^`n~V~3TG!x3e1G8J_lcjl7N>sCxKaJw|C=%RhTDg{d)6-'
    'g3psIZ85b4*AMzk~5t+Jn8h^<(NBkyhDgHn6D&~N$CF_Rem%6tTzmMOC&Cd9HN7gSJ7i)SP@f*gJvhV06^2>8pT(idNeBH(&z-'
    'o*;Bv#Y(+F@k<TFV%Yv9)@*_iFNk>9q<gYq^IR|LJ?re%vvnif^i4@8YaKGWVa>wB#Ra&Wram|Hb<n`Cf?$HMMf)F5|K5C|tLdxi'
    't;`hP;T=aBlPx18<`i<A*=|Vf&AM^rQA){NfkNql}^Z=p1>j)qH^U;NEerJ_qY&;jI=f<{CZekK_Nw3&0!sEazsd$a_oo*2!FW$;'
    '>!ra#FSu^KE$C3)jeU<q~mT?g>=yRa|f6`dHu38V@s$>DmhG2=Nx|&ah#_+D48X+4L%g7oT(Hd<s|n&ZeK3xiKB%v@clyw?E_h5C'
    '5;ROXER~m-E}iQfvFcy*2*J+@;?%=Vbi4&bQ*Xj6-'
    'wpjEz@0V$!*~hq&_`kRj(_8P(j81MA;v+%0>m=>IGu+X&Zixz5Y@B;Tt?|5*K=e%PLI0{+L?spm-gryYqaDdvb?Ic7<0&GmxTGjz'
    'zYY5zaZc^$pBUEuYMw=}U=_R+4*s%zo~*1x4bYHmBOQD0+S2gmR=o1fCyrRS4*ENv(1@3KE1(C?(d-'
    'h7XYb=uE1_eRQ*HIf>*_MiOZC*q>~$AA3CcIuIS^{ZbAdt-f$d4b+Z9_Wtqd(k2Mb<c%r-'
    'YJ(l^Zq(>G#r9;54gmI8hpw=Xx0&S)qGs81F+1^_gUw@=iV!OOyc+83o%bODrfYehqfy>jl5xc|CU(E{-'
    '*wD$Bu1{zqD_kawFpXedOQ892`sT9laMaPheF$m>c}3^dDr9w~p;_|3Qw(!u@QWpH<hxA<K-'
    'bbS9sZct79(Hhx6zDRBkft9Y&4GrZA9<dHaJ6Yui>a3pS%*m$#Fb?saBDOUX(To&x<rc9Xu))Rizr1;&3n|h<d^>9@AYWw!VW4te'
    'GF~OGMSAfeEyF%^~d8AvF+sS??-V0sC_AVIucYpVHjP`4<y;fX%*g)GZ?t$l^ui<jo8!}1m1;z4-'
    '?S1soM}zg4A)YV%&H3bxBN|_49$}}+VZ~-TzXMzbyUcnIw+#IWS&uAJ<{R<U!hbq7K1ZF#d~t}~dFKQ$4q-'
    '>&MrY2vp*$;k7f_1|Z^PEDg_FU9ytqx9c8E8<yBj`__3Cx7bLYOW{p4;gb3Tx`hjY)|)Hk}vWZg5=b<o&1&OKv<ovx=rb|t3usyG'
    '8a`DE~%Wpb0@q#@4Z8YXlX{E|9uFb?>@oP%rM+B`IlskmPc@A28}r6=s8aCoZEqIv~<_SqMmAAImh?8hz&!+ibq^YrQwmPGv)`yT'
    'U4z_ZIpt{V6%;~o;z+)F<>@t@vy+Z_#d%{|6uWKL9LcZ_4ZUfg`n700f1NPFq3M=rH8n!_J_@WC~gtMvfSB)&=P3%`eWAh;2>*Yz'
    ';YE3qu=euKoR?1SPP^l{fslML^=3;cY1N9^6n?`+MR_dr+ZoA9C|N9f(KuWQ}9&0X}$fVYmmM)bIN>Z#|3eE#`Ybvzrnvp0`(yQ_'
    'WJu#xR|+%dYr_{}d|W0M1Y4P%$iop8;iWoPW%Ty4hTvi}2k<uzBr;pj0$k4NSsz7ujm@91kpOch+n`%NB`W5RP{k?_}1JLmc%{J~'
    'pqy@g(e9jt%h7k2Qui4*T(@1yyWam_(%MQc3dqmMp?KSc2nYTv+*z(n1DaA5tLb3?pd*8Hbg=c`^BoI~Bup~Bx})A$Z}7dC*HD(f'
    ')(f7HQM{F7IVzk?kSJBEAq%$YNqE1ZWp9{G>NkErcxfw5(smhSJxi|-'
    'DBKkQq?{5wDW^uLrtPrf<%^23IWQa{4d!)Su!2M!nG5`Kq)^>5~(^vE?&YbmlrW_4cz=B|4=ReTx^M@{zlr4|m|w2f5%sP9nEHBe'
    'W+^>^ZbiHpmpz(>Rez;y%nBHZQF9frLFHwv9225_%x+Q*E!Cv3#r#?B!p);jb2C#P)FSFg^KM)$J+pa$~H$BjQnTqgHD`VHq+)qO'
    '~jVfrXdKTOsi*E>;%P0ar{zxmD8>g!<gQSJ@%!nJbf0J36VfKAQ%Lt(_MNyLlrmwS3vN_JDH&J_O?Js#-'
    '=HGB3#jTI}@AF!zxL{0<iF|!s}^5WX+{(8jv?RQvisdwtlMC~e%!P1-'
    '`lk2o%S=9VyK3}s>Njz8QM6DsRWgb%hI*<$bN`18k!;h#h!?v=QLQWYs)4FB8nY!nL_cMjtXRZ2Q72bs%s_Ccxjd|$WQ^yVKI=IB'
    '!njVAPL-'
    '05B&An>fgOJZ=?`eIGqt}ueXCcol&Q1L=Tqk7wD06Yu?}2_M#$&)9z$4%+<hRTxhhE_~bFIWFz#`!m#SW6c1@8*$w0$4vy1PEgd2'
    'r~7_W@ov-9w8S4)b>!&n+?PNBi-qgN0Nz_3GRB>Z>oS*7Dprc(LE=dhx{<$bnNogV?{wrt@EXC+wheEQMcU8@Wc-RBBe?asT3rFP'
    'Kk?>!mLuUjrGU4_qH|jJc(~bn3D8-'
    '^knbzWC4Joeb7!zR%HksAELQU87@i(=@R^_OQ<JL>_f6toxJHuQ^8mKR)%;{0)tMxR*iMH=R&TjyY&zz=;_8aaRoTd&cPe(H&x8*'
    '>6_&*1b!Zi_C3&W1kDQk?Y_Z(FtFl<G&e`m5lja<`=KozvnaNmoi_d<zDy2bc~h9oR@Rj`7QSA>`yaCqTw0Azd)A@_P16xt+w6x$'
    '9y->ug2b*o(Nnc@&!wTe}Cl2v9WH;4-Gv*Ux=p?2V6jonDl~m%e-'
    '0W6tR0^Ug%23JC##~@5cI;eay9I<h#Tg9iL?1<2|JLzPQFZMp(zCOC8j*LF4(Bq4`Z*v*H|h{@47*_zBoM{v%@|vccJ}M|#Kk5v$'
    'AE;6`rV-'
    '#Wg8oHuS<ue#Fv?=P~NF{9+pz^MYSU+FtMSNfN+`?di*UgGkyUZ5jfhj}ZxZu7IJ?zPO}Hn4`lyiJ9NX?qisW54crule5kxCt-'
    'CORS3-htC?u75cBlr@PE?hHUV!;PJ%&#BLLB%J>!6@&5ph>t;y'
)

def banner_rgb_256(red, green, blue):
    def channel(value):
        if value < 48:
            return 0
        if value < 115:
            return 1
        return min(5, round((value - 55) / 40))

    r, g, b = channel(red), channel(green), channel(blue)
    cube_index = 16 + 36 * r + 6 * g + b
    gray = round((red + green + blue) / 3)
    gray_index = min(23, max(0, round((gray - 8) / 10)))
    cube_rgb = (r * 51, g * 51, b * 51)
    cube_distance = sum(
        (a - b) ** 2 for a, b in zip((red, green, blue), cube_rgb)
    )
    gray_value = 8 + gray_index * 10
    gray_distance = sum(
        (v - gray_value) ** 2 for v in (red, green, blue)
    )
    return cube_index if cube_distance <= gray_distance else 232 + gray_index


def get_banner_payload():
    compressed = base64.b85decode(BANNER_PAYLOAD.encode("ascii"))
    raw = zlib.decompress(compressed)
    frame_size = BANNER_WIDTH * BANNER_HEIGHT * BANNER_BYTES_PER_CELL
    if len(raw) != frame_size * BANNER_FRAME_COUNT:
        raise ValueError("Frame data size mismatch.")
    return raw, frame_size


def make_banner_frame(raw, offset, no_color, true_color):
    frame_size = BANNER_WIDTH * BANNER_HEIGHT * BANNER_BYTES_PER_CELL
    data = raw[offset:offset + frame_size]
    lines = []

    if BANNER_MODE == "normal" or no_color:
        for row in range(BANNER_HEIGHT):
            start = row * BANNER_WIDTH * BANNER_BYTES_PER_CELL
            line = bytes(
                data[start + col * BANNER_BYTES_PER_CELL]
                for col in range(BANNER_WIDTH)
            ).decode("ascii")
            lines.append(line)
        return "\n".join(lines)

    for row in range(BANNER_HEIGHT):
        parts = []
        previous_color = None
        start = row * BANNER_WIDTH * 4
        for col in range(BANNER_WIDTH):
            pos = start + col * 4
            char = chr(data[pos])
            red, green, blue = data[pos + 1:pos + 4]
            color = (red, green, blue)
            if color != previous_color:
                if true_color:
                    parts.append(f"\033[38;2;{red};{green};{blue}m")
                else:
                    parts.append(f"\033[38;5;{banner_rgb_256(red, green, blue)}m")
                previous_color = color
            parts.append(char)
        parts.append("\033[0m")
        lines.append("".join(parts))
    return "\n".join(lines)



def start_terminal_banner():
    """Animate the header in place and keep a colored, stable menu below it."""
    menu_lines = [
        f"{BOLD}{CYAN}  LEMRENS{RESET} {DIM}| ASCII media toolkit{RESET}",
        f"{BLUE}  اكتب اسم الأداة مباشرة داخل تيليجرام:{RESET}",
        f"{GREEN}  image / صورة{RESET}   {WHITE}تحويل الصور إلى ASCII{RESET}",
        f"{MAGENTA}  video / فيديو{RESET}  {WHITE}تحويل الفيديو إلى ASCII{RESET}",
        f"{YELLOW}  cancel / إلغاء{RESET}  {WHITE}إلغاء العملية الحالية{RESET}",
        f"{DIM}  يمكنك أيضًا إرسال صورة أو فيديو مباشرة دون أي أمر.{RESET}",
    ]
    if not sys.stdout.isatty():
        print(f"{BOLD}{CYAN}Lemrens{RESET} | ASCII media toolkit")
        for line in menu_lines[1:]:
            print(line)
        return None, None

    try:
        raw, frame_size = get_banner_payload()
    except Exception:
        # Still provide a usable static UI if the embedded animation cannot load.
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write(f"{BOLD}{CYAN}Lemrens{RESET} | ASCII media toolkit\n")
        for line in menu_lines[1:]:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        return None, None

    stop_event = threading.Event()
    frame_duration = 1.0 / BANNER_FPS
    true_color = (
        os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")
        or "truecolor" in os.environ.get("TERM", "").lower()
        or "direct" in os.environ.get("TERM", "").lower()
    )

    # Reserve the first BANNER_HEIGHT rows for the animation.
    sys.stdout.write("\033[2J\033[H\033[?25l")
    sys.stdout.flush()

    def render():
        frame_number = 0
        cycle_start = time.perf_counter()
        while not stop_event.is_set():
            target_time = cycle_start + frame_number * frame_duration
            delay = target_time - time.perf_counter()
            if delay > 0 and stop_event.wait(delay):
                break
            frame = make_banner_frame(
                raw,
                frame_number * frame_size,
                no_color=False,
                true_color=true_color,
            )
            # Save and restore the cursor so the prompt/menu stay in place.
            sys.stdout.write("\033[s\033[H" + frame + "\033[u")
            sys.stdout.flush()
            frame_number += 1
            if frame_number >= BANNER_FRAME_COUNT:
                frame_number = 0
                cycle_start += BANNER_FRAME_COUNT * frame_duration

    thread = threading.Thread(target=render, name="lemrens-terminal-banner", daemon=True)
    thread.start()

    sys.stdout.write(f"\033[{BANNER_HEIGHT + 2};1H")
    sys.stdout.write(f"{DIM}{'─' * 58}{RESET}\n")
    for line in menu_lines:
        sys.stdout.write(line + "\n")
    sys.stdout.write(f"{DIM}{'─' * 58}{RESET}\n")
    sys.stdout.flush()
    return stop_event, thread

def stop_terminal_banner(banner_state):
    if not banner_state:
        return
    stop_event, thread = banner_state
    if stop_event:
        stop_event.set()
    if thread:
        thread.join(timeout=1.0)
    if sys.stdout.isatty():
        sys.stdout.write("\033[0m\033[?25h\n")
        sys.stdout.flush()


MAX_INPUT_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MAX_VIDEO_PIXELS = 40_000_000
MAX_ASCII_ROWS = 300

MAX_VIDEO_SECONDS = 8
VIDEO_FPS = 24
MAX_SOURCE_FPS = 120
MAX_VIDEO_FRAMES = MAX_VIDEO_SECONDS * VIDEO_FPS
MAX_SCRIPT_BYTES = 45 * 1024 * 1024

ASCII_CHARS = "@%#*+=-:. "
IMAGE_WIDTH_OPTIONS = (60, 100, 140)
VIDEO_WIDTH_OPTIONS = (40, 60, 80)

PROGRESS_STAGES = {
    "validation": {"label": "Validating input", "weight": 5},
    "extract": {"label": "Extracting frames", "weight": 10},
    "ascii": {"label": "Converting to ASCII", "weight": 35},
    "preview": {"label": "Rendering previews", "weight": 10},
    "mp4": {"label": "Encoding MP4", "weight": 20},
    "python": {"label": "Building Python script", "weight": 10},
    "upload": {"label": "Uploading files", "weight": 10},
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.WARNING,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.ERROR)
# Hide routine connection/polling chatter in the terminal; real errors can still appear.
logging.disable(logging.WARNING)
logger = logging.getLogger("lemrens")
logger.setLevel(logging.ERROR)


def run_command(command, timeout=180):
    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Media processing timed out.") from error
    except subprocess.CalledProcessError as error:
        details = error.stderr or b""
        if isinstance(details, bytes):
            details = details.decode("utf-8", errors="replace")
        logger.error("Command failed: %s", details[-2000:])
        raise RuntimeError("FFmpeg failed to process the file.") from error


def report_progress(progress_callback, stage, percent, detail=""):
    if progress_callback is None:
        return
    try:
        progress_callback(stage, max(0.0, min(100.0, float(percent))), detail)
    except Exception:
        logger.exception("Progress callback failed for stage %s", stage)


def _parse_ffmpeg_time_us(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _parse_ffmpeg_clock(value):
    try:
        hours_text, minutes_text, seconds_text = value.strip().split(":", 2)
        return max(
            0.0,
            int(hours_text) * 3600
            + int(minutes_text) * 60
            + float(seconds_text),
        )
    except (TypeError, ValueError):
        return None


def run_ffmpeg_with_progress(
    command,
    duration_seconds,
    progress_callback=None,
    stage="extract",
    timeout=180,
):
    if not command or len(command) < 2:
        raise ValueError("Invalid FFmpeg command.")

    monitored_command = list(command[:-1]) + [
        "-progress", "pipe:1", "-nostats", command[-1]
    ]

    started_at = time.monotonic()
    last_percent = 0.0
    block_time_us = None
    block_clock_seconds = None
    process = None

    with tempfile.TemporaryFile() as error_file:
        try:
            process = subprocess.Popen(
                monitored_command,
                stdout=subprocess.PIPE,
                stderr=error_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as error:
            raise RuntimeError(
                "Could not start FFmpeg. Make sure it is installed and in PATH."
            ) from error

        selector = selectors.DefaultSelector()
        try:
            if process.stdout is not None:
                selector.register(process.stdout, selectors.EVENT_READ)

            stream_finished = False
            while not stream_finished:
                if timeout and time.monotonic() - started_at > timeout:
                    process.kill()
                    process.wait()
                    raise RuntimeError("FFmpeg processing timed out.")

                events = selector.select(timeout=0.25)
                if not events:
                    if process.poll() is not None:
                        continue
                    continue

                for key, _ in events:
                    line = key.fileobj.readline()
                    if line == "":
                        try:
                            selector.unregister(key.fileobj)
                        except Exception:
                            pass
                        stream_finished = True
                        break

                    line = line.strip()
                    if "=" not in line:
                        continue

                    name, value = line.split("=", 1)

                    if name in ("out_time_us", "out_time_ms"):
                        parsed = _parse_ffmpeg_time_us(value)
                        if parsed is not None:
                            block_time_us = parsed
                    elif name == "out_time":
                        block_clock_seconds = _parse_ffmpeg_clock(value)
                    elif name == "progress":
                        if duration_seconds > 0:
                            if block_time_us is not None:
                                elapsed = block_time_us / 1_000_000.0
                            elif block_clock_seconds is not None:
                                elapsed = block_clock_seconds
                            else:
                                elapsed = 0.0

                            last_percent = max(
                                last_percent,
                                min(99.0, max(
                                    0.0, elapsed / duration_seconds * 100.0
                                )),
                            )
                            report_progress(
                                progress_callback, stage, last_percent,
                                "FFmpeg processing",
                            )
                        block_time_us = None
                        block_clock_seconds = None

            return_code = process.wait(timeout=5)

        except BaseException:
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass
            raise
        finally:
            selector.close()
            if process.stdout is not None:
                process.stdout.close()

        error_file.seek(0)
        details = error_file.read().decode("utf-8", errors="replace")

    if return_code != 0:
        logger.error("FFmpeg failed: %s", details[-3000:])
        raise RuntimeError("FFmpeg failed to process the file.")

    report_progress(progress_callback, stage, 100, "Complete")


def make_ascii_art(image_bytes, requested_width, mode):
    with Image(blob=image_bytes) as image:
        if image.width <= 0 or image.height <= 0:
            raise ValueError("Invalid image dimensions.")
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("Image too large. Maximum is 25 megapixels.")

        image.auto_orient()
        source_width, source_height = image.width, image.height
        ascii_width = requested_width
        ascii_height = max(
            1, int(ascii_width * source_height / source_width * 0.48)
        )

        if ascii_height > MAX_ASCII_ROWS:
            ascii_height = MAX_ASCII_ROWS
            ascii_width = max(
                8,
                min(
                    requested_width,
                    int(ascii_height * source_width / source_height / 0.48),
                ),
            )
            ascii_height = max(
                1, int(ascii_width * source_height / source_width * 0.48)
            )

        with image.clone() as gray:
            if mode == "sharp":
                gray.sigmoidal_contrast(
                    sharpen=True, strength=5,
                    midpoint=0.5 * gray.quantum_range,
                )
                gray.unsharp_mask(
                    radius=0, sigma=1.0, amount=1.15, threshold=0.02
                )
            gray.transform_colorspace("gray")
            gray.auto_level()
            gray.resize(ascii_width, ascii_height)
            gray_pixels = gray.export_pixels(
                0, 0, ascii_width, ascii_height, "I", "char"
            )

        ramp_last = len(ASCII_CHARS) - 1

        if mode in ("color", "sharp"):
            with image.clone() as resized:
                resized.resize(ascii_width, ascii_height)
                if mode == "sharp":
                    resized.modulate(brightness=96, saturation=165, hue=100)
                    resized.sigmoidal_contrast(
                        sharpen=True, strength=5,
                        midpoint=0.5 * resized.quantum_range,
                    )
                    resized.unsharp_mask(
                        radius=0, sigma=1.0, amount=1.2, threshold=0.02
                    )
                rgb_pixels = resized.export_pixels(
                    0, 0, ascii_width, ascii_height, "RGB", "char"
                )

            rows = []
            pixel_index = 0
            for row in range(ascii_height):
                cells = []
                for col in range(ascii_width):
                    gray_value = max(
                        0, min(255, int(gray_pixels[row * ascii_width + col]))
                    )
                    char = ASCII_CHARS[gray_value * ramp_last // 255]
                    red = int(rgb_pixels[pixel_index])
                    green = int(rgb_pixels[pixel_index + 1])
                    blue = int(rgb_pixels[pixel_index + 2])
                    pixel_index += 3
                    cells.append((char, red, green, blue))
                rows.append(cells)
            return rows, ascii_width, ascii_height

        lines = []
        for row in range(ascii_height):
            start = row * ascii_width
            lines.append("".join(
                ASCII_CHARS[
                    max(0, min(255, int(gray_pixels[index])))
                    * ramp_last // 255
                ]
                for index in range(start, start + ascii_width)
            ))
        return lines, ascii_width, ascii_height


def plain_text(ascii_art, mode):
    if mode in ("color", "sharp"):
        return "\n".join("".join(cell[0] for cell in row) for row in ascii_art)
    return "\n".join(ascii_art)


def ansi_text(ascii_art, mode):
    if mode not in ("color", "sharp"):
        return plain_text(ascii_art, mode)

    output_lines = []
    for row in ascii_art:
        parts = []
        previous_color = None
        for char, red, green, blue in row:
            current_color = (red, green, blue)
            if current_color != previous_color:
                parts.append(f"\033[38;2;{red};{green};{blue}m")
                previous_color = current_color
            parts.append(char)
        parts.append("\033[0m")
        output_lines.append("".join(parts))
    return "\n".join(output_lines)


def make_preview(ascii_art, columns, mode):
    margin, char_width, line_height = 12, 8, 15
    rows = len(ascii_art)
    width = margin * 2 + char_width * columns
    height = margin * 2 + line_height * rows
    if height % 2:
        height += 1

    with Image(
        width=width, height=height, background=Color("#0c0e12")
    ) as preview:
        with Drawing() as draw:
            draw.font = "DejaVu-Sans-Mono"
            draw.font_size = 12
            draw.text_antialias = False

            if mode in ("color", "sharp"):
                for row_index, row in enumerate(ascii_art):
                    y = margin + row_index * line_height + 11
                    run_start = None
                    run_color = None
                    run_chars = []

                    def flush_run():
                        nonlocal run_start, run_color, run_chars
                        if run_chars and run_start is not None:
                            red, green, blue = run_color
                            draw.fill_color = Color(
                                f"#{red:02x}{green:02x}{blue:02x}"
                            )
                            draw.text(
                                margin + run_start * char_width,
                                y,
                                "".join(run_chars),
                            )
                        run_start = None
                        run_color = None
                        run_chars = []

                    for col_index, cell in enumerate(row):
                        char, red, green, blue = cell
                        current_color = (red, green, blue)
                        if char == " ":
                            flush_run()
                            continue
                        if current_color != run_color:
                            flush_run()
                            run_start = col_index
                            run_color = current_color
                        run_chars.append(char)
                    flush_run()
            else:
                draw.fill_color = Color("#ebeff5")
                for index, line in enumerate(ascii_art):
                    draw.text(margin, margin + index * line_height + 11, line)

            draw(preview)
            output = io.BytesIO()
            preview.format = "png"
            preview.save(file=output)

    output.seek(0)
    output.name = "ascii_preview.png"
    return output


def make_python_file(ascii_art, mode):
    if mode in ("color", "sharp"):
        code = (
            "#!/usr/bin/env python3\n"
            "# Generated by ASCII Art Bot\n\n"
            f"ASCII_ROWS = {ascii_art!r}\n\n"
            "if __name__ == '__main__':\n"
            "    for row in ASCII_ROWS:\n"
            "        output = []\n"
            "        previous_color = None\n"
            "        for char, red, green, blue in row:\n"
            "            color = (red, green, blue)\n"
            "            if color != previous_color:\n"
            "                output.append(f'\\033[38;2;{red};{green};{blue}m')\n"
            "                previous_color = color\n"
            "            output.append(char)\n"
            "        output.append('\\033[0m')\n"
            "        print(''.join(output))\n"
        )
    else:
        code = (
            "#!/usr/bin/env python3\n"
            "# Generated by ASCII Art Bot\n\n"
            f"ASCII_ART = {plain_text(ascii_art, mode)!r}\n\n"
            "if __name__ == '__main__':\n"
            "    print(ASCII_ART)\n"
        )
    output = io.BytesIO(code.encode("utf-8"))
    output.name = "ascii_art.py"
    output.seek(0)
    return output


def make_text_file(ascii_art, mode):
    output = io.BytesIO(ansi_text(ascii_art, mode).encode("utf-8"))
    output.name = "ascii_art.txt"
    output.seek(0)
    return output


def pack_ascii_frame(ascii_art, mode):
    if mode == "normal":
        return bytes(ord(char) for row in ascii_art for char in row)
    return bytes(
        value
        for row in ascii_art
        for cell in row
        for value in (
            ord(cell[0]),
            max(0, min(255, int(cell[1]))),
            max(0, min(255, int(cell[2]))),
            max(0, min(255, int(cell[3]))),
        )
    )


def make_video_python_file(
    frames, width, height, mode, fps=VIDEO_FPS
):
    if not frames:
        raise ValueError("No frames to build Python file.")
    if width <= 0 or height <= 0:
        raise ValueError("Invalid ASCII frame dimensions.")
    if mode not in ("normal", "color", "sharp"):
        raise ValueError("Unsupported video mode.")

    fps_fraction = Fraction(str(fps)).limit_denominator(100000)
    if not Fraction(1, 10) <= fps_fraction <= MAX_SOURCE_FPS:
        raise ValueError("Invalid frame rate.")

    fps_expression = (
        f"({fps_fraction.numerator} / {fps_fraction.denominator})"
    )

    bytes_per_cell = 1 if mode == "normal" else 4
    expected_frame_size = width * height * bytes_per_cell
    if any(len(frame) != expected_frame_size for frame in frames):
        raise ValueError("ASCII frame sizes do not match.")

    compressed = zlib.compress(b"".join(frames), level=9)
    encoded = base64.b85encode(compressed).decode("ascii")
    encoded_lines = textwrap.wrap(encoded, 100)
    embedded_data = "PAYLOAD = (\n" + "".join(
        f"    {line!r}\n" for line in encoded_lines
    ) + ")\n"

    player_code = r'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone looping ASCII video player."""

import argparse
import base64
import os
import sys
import time
import zlib

WIDTH = __WIDTH__
HEIGHT = __HEIGHT__
FPS = __FPS__
MODE = __MODE__
FRAME_COUNT = __FRAME_COUNT__
BYTES_PER_CELL = __BYTES_PER_CELL__

__PAYLOAD_PLACEHOLDER__

def rgb_256(red, green, blue):
    def channel(value):
        if value < 48:
            return 0
        if value < 115:
            return 1
        return min(5, round((value - 55) / 40))

    r, g, b = channel(red), channel(green), channel(blue)
    cube_index = 16 + 36 * r + 6 * g + b
    gray = round((red + green + blue) / 3)
    gray_index = min(23, max(0, round((gray - 8) / 10)))
    cube_rgb = (r * 51, g * 51, b * 51)
    cube_distance = sum(
        (a - b) ** 2 for a, b in zip((red, green, blue), cube_rgb)
    )
    gray_value = 8 + gray_index * 10
    gray_distance = sum(
        (v - gray_value) ** 2 for v in (red, green, blue)
    )
    return cube_index if cube_distance <= gray_distance else 232 + gray_index


def get_payload():
    compressed = base64.b85decode(PAYLOAD.encode("ascii"))
    raw = zlib.decompress(compressed)
    frame_size = WIDTH * HEIGHT * BYTES_PER_CELL
    if len(raw) != frame_size * FRAME_COUNT:
        raise ValueError("Frame data size mismatch.")
    return raw, frame_size


def make_frame(raw, offset, no_color, true_color):
    frame_size = WIDTH * HEIGHT * BYTES_PER_CELL
    data = raw[offset:offset + frame_size]
    lines = []

    if MODE == "normal" or no_color:
        for row in range(HEIGHT):
            start = row * WIDTH * BYTES_PER_CELL
            line = bytes(
                data[start + col * BYTES_PER_CELL]
                for col in range(WIDTH)
            ).decode("ascii")
            lines.append(line)
        return "\n".join(lines)

    for row in range(HEIGHT):
        parts = []
        previous_color = None
        start = row * WIDTH * 4
        for col in range(WIDTH):
            pos = start + col * 4
            char = chr(data[pos])
            red, green, blue = data[pos + 1:pos + 4]
            color = (red, green, blue)
            if color != previous_color:
                if true_color:
                    parts.append(f"\033[38;2;{red};{green};{blue}m")
                else:
                    parts.append(f"\033[38;5;{rgb_256(red, green, blue)}m")
                previous_color = color
            parts.append(char)
        parts.append("\033[0m")
        lines.append("".join(parts))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Looping ASCII video player"
    )
    parser.add_argument("--fps", type=float, default=FPS)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if not 0.1 <= args.fps <= 120:
        parser.error("FPS must be between 0.1 and 120.")

    raw, frame_size = get_payload()
    true_color = (
        not args.no_color
        and os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")
    )
    if not true_color and not args.no_color:
        term = os.environ.get("TERM", "").lower()
        true_color = "direct" in term or "truecolor" in term

    terminal = sys.stdout.isatty()
    frame_duration = 1.0 / args.fps
    cycle_duration = FRAME_COUNT * frame_duration
    cycle_start = time.perf_counter()
    frame_number = 0

    try:
        if terminal:
            sys.stdout.write("\033[2J\033[H\033[?25l")
            sys.stdout.flush()

        while True:
            target_time = cycle_start + frame_number * frame_duration
            remaining = target_time - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)

            frame = make_frame(
                raw, frame_number * frame_size, args.no_color, true_color
            )
            if terminal:
                sys.stdout.write("\033[H" + frame + "\033[J")
            else:
                sys.stdout.write(frame + "\n")
            sys.stdout.flush()

            frame_number += 1
            if frame_number >= FRAME_COUNT:
                frame_number = 0
                cycle_start += cycle_duration

    except KeyboardInterrupt:
        pass
    finally:
        try:
            sys.stdout.write("\033[0m")
            if terminal:
                sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        except (OSError, BrokenPipeError):
            pass


if __name__ == "__main__":
    main()
'''

    player_code = (
        player_code
        .replace("__WIDTH__", str(width))
        .replace("__HEIGHT__", str(height))
        .replace("__FPS__", fps_expression)
        .replace("__MODE__", repr(mode))
        .replace("__FRAME_COUNT__", str(len(frames)))
        .replace("__BYTES_PER_CELL__", str(bytes_per_cell))
        .replace("__PAYLOAD_PLACEHOLDER__", embedded_data.rstrip())
    )

    code_bytes = player_code.encode("utf-8")
    if len(code_bytes) > MAX_SCRIPT_BYTES:
        raise ValueError(
            "Compressed video data is too large. Try a lower resolution "
            "or a simpler video."
        )

    compile(player_code, "ascii_video.py", "exec")
    output = io.BytesIO(code_bytes)
    output.name = "ascii_video.py"
    output.seek(0)
    return output


def _parse_frame_rate(value):
    try:
        rate = Fraction(str(value))
        if rate <= 0:
            return None
        return rate.limit_denominator(100000)
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _ffmpeg_frame_rate(rate):
    return f"{rate.numerator}/{rate.denominator}"


def _format_frame_rate(rate):
    number = float(rate)
    if abs(number - round(number)) < 0.001:
        return f"{round(number)}"
    return f"{number:.3f}".rstrip("0").rstrip(".")


def probe_video(video_path):
    result = run_command(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,duration,avg_frame_rate,r_frame_rate",
            "-of", "json", video_path,
        ],
        timeout=30,
    )

    try:
        data = json.loads(result.stdout.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Could not read video information.") from error

    streams = data.get("streams", [])
    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        raise ValueError("File does not contain a valid video stream.")

    try:
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
    except (TypeError, ValueError):
        width, height = 0, 0

    if width <= 0 or height <= 0:
        raise ValueError("Invalid video dimensions.")
    if width * height > MAX_VIDEO_PIXELS:
        raise ValueError("Video dimensions too large. Maximum is 40 megapixels.")

    format_info = data.get("format", {})
    try:
        duration = float(format_info.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0

    if duration <= 0:
        for stream in streams:
            try:
                duration = max(duration, float(stream.get("duration") or 0))
            except (TypeError, ValueError):
                pass

    if duration <= 0:
        raise ValueError("Could not determine video duration.")

    source_fps = (
        _parse_frame_rate(video_stream.get("avg_frame_rate"))
        or _parse_frame_rate(video_stream.get("r_frame_rate"))
        or Fraction(VIDEO_FPS, 1)
    )
    source_fps = min(source_fps, Fraction(MAX_SOURCE_FPS, 1))

    has_audio = any(
        stream.get("codec_type") == "audio" for stream in streams
    )
    return duration, width, height, has_audio, source_fps


def convert_video_to_ascii(
    video_bytes,
    requested_width,
    mode,
    progress_callback=None,
    fps_mode="fixed",
):
    if not video_bytes:
        raise ValueError("Video file is empty.")
    if len(video_bytes) > MAX_INPUT_BYTES:
        raise ValueError("Video exceeds the 15 MB limit.")
    if requested_width not in VIDEO_WIDTH_OPTIONS:
        raise ValueError("Unsupported video resolution.")
    if mode not in ("normal", "color", "sharp"):
        raise ValueError("Unsupported conversion mode.")
    if fps_mode not in ("fixed", "source"):
        raise ValueError("Unsupported FPS option.")

    report_progress(progress_callback, "validation", 0, "Checking file")

    with tempfile.TemporaryDirectory(prefix="ascii_video_") as temp:
        work = Path(temp)
        input_path = work / "input_video.bin"
        frames_directory = work / "frames"
        ascii_directory = work / "ascii_frames"
        output_path = work / "ascii_video.mp4"

        frames_directory.mkdir()
        ascii_directory.mkdir()
        input_path.write_bytes(video_bytes)

        duration, _, _, has_audio, source_fps = probe_video(str(input_path))
        if duration > MAX_VIDEO_SECONDS:
            raise ValueError(
                f"Video duration is {duration:.1f}s. "
                f"Maximum is {MAX_VIDEO_SECONDS}s."
            )

        target_fps = (
            source_fps if fps_mode == "source" else Fraction(VIDEO_FPS, 1)
        )
        target_fps_text = _ffmpeg_frame_rate(target_fps)
        max_frames = max(
            1, math.ceil(MAX_VIDEO_SECONDS * float(target_fps))
        )

        report_progress(
            progress_callback, "validation", 100,
            f"Duration {duration:.2f}s, FPS {_format_frame_rate(target_fps)}",
        )

        frame_pattern = str(frames_directory / "source_%05d.jpg")
        extraction_command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
            "-vf",
            f"fps={target_fps_text},"
            f"scale={requested_width * 2}:-2:flags=bilinear",
            "-frames:v", str(max_frames),
            "-q:v", "4",
            frame_pattern,
        ]

        report_progress(progress_callback, "extract", 0, "Starting extraction")
        run_ffmpeg_with_progress(
            extraction_command,
            duration_seconds=duration,
            progress_callback=progress_callback,
            stage="extract",
            timeout=180,
        )

        source_frames = sorted(
            glob.glob(str(frames_directory / "source_*.jpg"))
        )[:max_frames]
        if not source_frames:
            raise ValueError("Could not extract frames from video.")

        total_frames = len(source_frames)
        packed_frames = []
        frame_width = None
        frame_height = None
        ascii_pattern = str(ascii_directory / "ascii_%05d.png")

        report_progress(progress_callback, "ascii", 0, "Starting conversion")

        for index, source_frame in enumerate(source_frames, start=1):
            report_progress(
                progress_callback, "ascii",
                ((index - 1) / total_frames) * 100,
                f"Frame {index}/{total_frames}",
            )

            with open(source_frame, "rb") as frame_file:
                frame_bytes = frame_file.read()

            ascii_art, actual_width, actual_height = make_ascii_art(
                frame_bytes, requested_width, mode
            )

            if frame_width is None:
                frame_width, frame_height = actual_width, actual_height
            elif (actual_width, actual_height) != (frame_width, frame_height):
                raise ValueError("Frame dimensions changed during processing.")

            packed_frames.append(pack_ascii_frame(ascii_art, mode))
            report_progress(
                progress_callback, "ascii",
                index / total_frames * 100,
                f"{index}/{total_frames} frames",
            )

            report_progress(
                progress_callback, "preview",
                (index - 1) / total_frames * 100,
                f"Preview {index}/{total_frames}",
            )
            preview = make_preview(ascii_art, actual_width, mode)
            output_frame = ascii_directory / f"ascii_{index:05d}.png"
            output_frame.write_bytes(preview.getvalue())
            report_progress(
                progress_callback, "preview",
                index / total_frames * 100,
                f"{index}/{total_frames} previews",
            )

            if index % 24 == 0:
                logger.info("Rendered %s video frames", index)

        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-framerate", target_fps_text,
            "-start_number", "1",
            "-i", ascii_pattern,
            "-i", str(input_path),
            "-map", "0:v:0",
        ]

        if has_audio:
            command.extend([
                "-map", "1:a:0",
                "-c:a", "aac",
                "-b:a", "96k",
                "-shortest",
            ])
        else:
            command.append("-an")

        output_duration = len(source_frames) / float(target_fps)
        command.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", target_fps_text,
            "-movflags", "+faststart",
            "-t", f"{output_duration:.6f}",
            str(output_path),
        ])

        report_progress(progress_callback, "mp4", 0, "Starting MP4 encoding")
        run_ffmpeg_with_progress(
            command,
            duration_seconds=output_duration,
            progress_callback=progress_callback,
            stage="mp4",
            timeout=240,
        )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("MP4 file was not created.")

        report_progress(progress_callback, "python", 0, "Compressing frames")
        python_file = make_video_python_file(
            packed_frames, frame_width, frame_height, mode, target_fps
        )
        report_progress(
            progress_callback, "python", 100,
            "Python script ready",
        )
        return output_path.read_bytes(), python_file.getvalue(), target_fps


def initial_progress_state():
    return {
        name: {"percent": 0.0, "status": "waiting", "detail": ""}
        for name in PROGRESS_STAGES
    }


def build_progress_text(states, final_status=None, error_message=""):
    total_weight = sum(info["weight"] for info in PROGRESS_STAGES.values())
    weighted_progress = sum(
        PROGRESS_STAGES[name]["weight"] * states[name]["percent"] / 100
        for name in PROGRESS_STAGES
    )
    is_complete = all(
        states[name]["status"] == "done" for name in PROGRESS_STAGES
    )
    percent = 100 if is_complete else min(
        99, int(weighted_progress / total_weight * 100)
    )
    filled = int(percent * 18 / 100)
    bar = "#" * filled + "-" * (18 - filled)

    if final_status == "success" and is_complete:
        title = "Conversion complete"
    elif final_status == "failure":
        title = "Conversion failed"
    elif all(
        states[name]["status"] == "done"
        for name in ("validation", "extract", "ascii", "preview", "mp4", "python")
    ):
        title = "Processing complete, uploading files"
    else:
        title = "Converting video to ASCII"

    lines = [title, "", f"[{bar}] {percent}%"]

    for name, info in PROGRESS_STAGES.items():
        state = states[name]
        if state["status"] == "done":
            status_text = "done"
        elif state["status"] == "running":
            status_text = f"running ({int(state['percent'])}%)"
        elif state["status"] == "failed":
            status_text = "failed"
        else:
            status_text = "waiting"
        lines.append(f"{info['label']}: {status_text}")

    if final_status == "failure" and error_message:
        lines.extend(["", f"Error: {error_message[:500]}"])
    return "\n".join(lines)


async def video_progress_updater(
    bot, chat_id, message_id, progress_queue, initial_text
):
    states = initial_progress_state()
    final_status = None
    error_message = ""
    last_text = initial_text
    last_edit_time = 0.0
    minimum_edit_interval = 1.25
    loop = asyncio.get_running_loop()

    async def try_edit(text):
        nonlocal last_text, last_edit_time
        if text == last_text:
            return
        try:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text
            )
            last_text = text
            last_edit_time = loop.time()
        except TelegramError as error:
            last_edit_time = loop.time()
            logger.warning("Could not edit progress message: %s", error)
        except Exception:
            last_edit_time = loop.time()
            logger.exception("Unexpected progress-message update error")

    while True:
        timeout = max(
            0.15, minimum_edit_interval - (loop.time() - last_edit_time)
        )
        event = None
        try:
            event = await asyncio.wait_for(progress_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        if event is None:
            pass
        elif event.get("type") == "stop":
            await try_edit(build_progress_text(states, final_status, error_message))
            return
        elif event.get("type") == "success":
            final_status = "success"
            states["upload"]["percent"] = 100
            states["upload"]["status"] = "done"
        elif event.get("type") == "failure":
            final_status = "failure"
            error_message = str(event.get("message") or "Unknown error")
            stage = event.get("stage")
            if stage in states:
                states[stage]["status"] = "failed"
                states[stage]["detail"] = error_message[:250]
        else:
            stage = event.get("stage")
            if stage in states:
                try:
                    percent = max(
                        0.0, min(100.0, float(event.get("percent", 0)))
                    )
                except (TypeError, ValueError):
                    percent = 0.0
                states[stage]["percent"] = max(
                    states[stage]["percent"], percent
                )
                states[stage]["detail"] = str(event.get("detail") or "")[:160]
                states[stage]["status"] = (
                    "done" if percent >= 100 else "running"
                )

        text = build_progress_text(states, final_status, error_message)
        if (
            final_status in ("success", "failure")
            or loop.time() - last_edit_time >= minimum_edit_interval
        ):
            await try_edit(text)


def clear_pending(context):
    for key in (
        "pending_image", "selected_mode", "pending_video",
        "selected_video_mode", "selected_fps_mode",
    ):
        context.user_data.pop(key, None)


async def send_with_retry(func, *args, retries=3, base_delay=2.0, **kwargs):
    """Call a Telegram API method, retrying on network errors.

    Rewinds any file-like objects between attempts so the upload
    does not send an empty file on retry.
    """
    last_error = None
    for attempt in range(retries):
        for value in list(kwargs.values()) + list(args):
            if hasattr(value, "seek") and hasattr(value, "read"):
                try:
                    value.seek(0)
                except Exception:
                    pass
        try:
            return await func(*args, **kwargs)
        except (TimedOut, NetworkError) as error:
            last_error = error
            if attempt < retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "Network error on attempt %d/%d, retrying in %.1fs: %s",
                    attempt + 1, retries, delay, error,
                )
                await asyncio.sleep(delay)
        except TelegramError:
            raise
    raise last_error


async def start(update, context):
    clear_pending(context)
    await update.effective_message.reply_text(
        "Lemrens — ASCII Media Toolkit\n\n"
        "اكتب اسم الأداة مباشرة، أو أرسل صورة/فيديو دون أوامر.\n\n"
        "Modes:\n"
        "- Normal: monochrome characters\n"
        "- Color: ANSI colors matching the original\n"
        "- Sharp: enhanced color and contrast\n\n"
        "Images: PNG preview, Python script, TXT file\n"
        "Video: MP4 and standalone animated Python player\n\n"
        f"Limits: video up to {MAX_VIDEO_SECONDS} seconds, "
        "file size 15 MB\n\n"
        "الأدوات المباشرة:\n"
        "image / صورة — تفعيل أداة الصور\n"
        "video / فيديو — تفعيل أداة الفيديو\n"
        "cancel / إلغاء — إلغاء العملية الحالية\n\n"
        "يمكنك إرسال الملف مباشرة دون تفعيل أي أداة مسبقًا."
    )


async def cancel(update, context):
    clear_pending(context)
    await update.effective_message.reply_text("تم إلغاء العملية.")


async def receive_image(update, context):
    message = update.effective_message
    if message is None:
        return

    if message.photo:
        media = message.photo[-1]
        telegram_file = await media.get_file()
        file_size = media.file_size
    elif message.document:
        media = message.document
        if not (media.mime_type or "").lower().startswith("image/"):
            await message.reply_text("Send a supported image file (PNG, JPG, WEBP).")
            return
        telegram_file = await media.get_file()
        file_size = media.file_size
    else:
        return

    if file_size and file_size > MAX_INPUT_BYTES:
        await message.reply_text("File size exceeds the 15 MB limit.")
        return

    status = await message.reply_text("Image received. Validating...")
    try:
        downloaded = io.BytesIO()
        await telegram_file.download_to_memory(out=downloaded)
        image_bytes = downloaded.getvalue()
        if len(image_bytes) > MAX_INPUT_BYTES:
            await status.edit_text("File size exceeds the 15 MB limit.")
            return
        with Image(blob=image_bytes) as check_image:
            if check_image.width * check_image.height > MAX_IMAGE_PIXELS:
                await status.edit_text("Image dimensions exceed the 25 MP limit.")
                return
            check_image.auto_orient()
    except (WandException, OSError, ValueError):
        logger.exception("Failed to read image")
        await status.edit_text("Could not read image. Try PNG, JPG, or WEBP.")
        return
    except Exception:
        logger.exception("Failed to download image")
        await status.edit_text("Failed to receive image. Try again.")
        return

    context.user_data["pending_image"] = image_bytes
    context.user_data.pop("selected_mode", None)
    user_id = message.from_user.id
    keyboard = [
        [InlineKeyboardButton("Normal", callback_data=f"mode:{user_id}:normal")],
        [
            InlineKeyboardButton("Color", callback_data=f"mode:{user_id}:color"),
            InlineKeyboardButton("Sharp", callback_data=f"mode:{user_id}:sharp"),
        ],
    ]
    await status.edit_text(
        "Image received. Choose a mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def receive_video(update, context):
    message = update.effective_message
    if message is None:
        return

    if message.video:
        media = message.video
        file_size = media.file_size
        if media.duration and media.duration > MAX_VIDEO_SECONDS:
            await message.reply_text(
                f"Video duration must not exceed {MAX_VIDEO_SECONDS} seconds."
            )
            return
    elif message.document:
        media = message.document
        if not (media.mime_type or "").lower().startswith("video/"):
            await message.reply_text("Send a supported video file (MP4, etc).")
            return
        file_size = media.file_size
    else:
        return

    if file_size and file_size > MAX_INPUT_BYTES:
        await message.reply_text("File size exceeds the 15 MB limit.")
        return

    status = await message.reply_text("Video received. Downloading...")
    try:
        telegram_file = await media.get_file()
        downloaded = io.BytesIO()
        await telegram_file.download_to_memory(out=downloaded)
        video_bytes = downloaded.getvalue()
        if not video_bytes:
            await status.edit_text("Video file is empty.")
            return
        if len(video_bytes) > MAX_INPUT_BYTES:
            await status.edit_text("File size exceeds the 15 MB limit.")
            return
    except Exception:
        logger.exception("Failed to download video")
        await status.edit_text("Failed to download the video. Try again.")
        return

    context.user_data["pending_video"] = video_bytes
    context.user_data.pop("selected_video_mode", None)
    user_id = message.from_user.id
    keyboard = [
        [InlineKeyboardButton("Normal", callback_data=f"video_mode:{user_id}:normal")],
        [
            InlineKeyboardButton("Color", callback_data=f"video_mode:{user_id}:color"),
            InlineKeyboardButton("Sharp", callback_data=f"video_mode:{user_id}:sharp"),
        ],
    ]
    await status.edit_text(
        "Video received. Choose a mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_mode(update, context):
    query = update.callback_query
    try:
        _, owner_text, mode = query.data.split(":", 2)
        owner_id = int(owner_text)
    except (ValueError, AttributeError):
        await query.answer("Invalid selection.", show_alert=True)
        return

    if query.from_user.id != owner_id:
        await query.answer("This selection is not yours.", show_alert=True)
        return
    if mode not in ("normal", "color", "sharp"):
        await query.answer("Invalid mode.", show_alert=True)
        return
    if not context.user_data.get("pending_image"):
        await query.answer("Image expired. Please send it again.", show_alert=True)
        return

    context.user_data["selected_mode"] = mode
    await query.answer()
    keyboard = [[
        InlineKeyboardButton(
            f"Low ({IMAGE_WIDTH_OPTIONS[0]})",
            callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[0]}",
        ),
        InlineKeyboardButton(
            f"Medium ({IMAGE_WIDTH_OPTIONS[1]})",
            callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[1]}",
        ),
        InlineKeyboardButton(
            f"High ({IMAGE_WIDTH_OPTIONS[2]})",
            callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[2]}",
        ),
    ]]
    mode_names = {
        "normal": "Normal", "color": "Color", "sharp": "Sharp"
    }
    await query.edit_message_text(
        f"Mode: {mode_names[mode]}\nChoose output width:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_video_mode(update, context):
    query = update.callback_query
    try:
        _, owner_text, mode = query.data.split(":", 2)
        owner_id = int(owner_text)
    except (ValueError, AttributeError):
        await query.answer("Invalid selection.", show_alert=True)
        return

    if query.from_user.id != owner_id:
        await query.answer("This selection is not yours.", show_alert=True)
        return
    if mode not in ("normal", "color", "sharp"):
        await query.answer("Invalid mode.", show_alert=True)
        return
    if not context.user_data.get("pending_video"):
        await query.answer("Video expired. Please send it again.", show_alert=True)
        return

    context.user_data["selected_video_mode"] = mode
    await query.answer()
    keyboard = [[
        InlineKeyboardButton(
            f"Low ({VIDEO_WIDTH_OPTIONS[0]})",
            callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[0]}",
        ),
        InlineKeyboardButton(
            f"Medium ({VIDEO_WIDTH_OPTIONS[1]})",
            callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[1]}",
        ),
        InlineKeyboardButton(
            f"High ({VIDEO_WIDTH_OPTIONS[2]})",
            callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[2]}",
        ),
    ]]
    mode_names = {
        "normal": "Normal", "color": "Color", "sharp": "Sharp"
    }
    await query.edit_message_text(
        f"Mode: {mode_names[mode]}\nChoose output width:\n\n"
        "Higher widths require more time and resources.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_video_fps(update, context):
    query = update.callback_query
    try:
        _, owner_text, width_text = query.data.split(":", 2)
        owner_id = int(owner_text)
        width = int(width_text)
    except (ValueError, AttributeError):
        await query.answer("Invalid selection.", show_alert=True)
        return

    if query.from_user.id != owner_id:
        await query.answer("This selection is not yours.", show_alert=True)
        return
    if width not in VIDEO_WIDTH_OPTIONS:
        await query.answer("Unsupported width.", show_alert=True)
        return
    if not context.user_data.get("pending_video"):
        await query.answer("Video expired. Please send it again.", show_alert=True)
        return

    context.user_data["selected_video_width"] = width
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "Source FPS",
                callback_data=f"videoascii:{owner_id}:{width}:source",
            )
        ],
        [
            InlineKeyboardButton(
                "24 FPS",
                callback_data=f"videoascii:{owner_id}:{width}:fixed",
            )
        ],
    ]
    await query.edit_message_text(
        "Choose frame rate:\n\n"
        f"Source FPS: match the original rate (max {MAX_SOURCE_FPS} FPS)\n"
        "24 FPS: fewer frames, faster processing",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def render_choice(update, context):
    query = update.callback_query
    try:
        _, owner_text, width_text = query.data.split(":", 2)
        owner_id, width = int(owner_text), int(width_text)
    except (ValueError, AttributeError):
        await query.answer("Invalid selection.", show_alert=True)
        return

    if query.from_user.id != owner_id:
        await query.answer("This selection is not yours.", show_alert=True)
        return
    if width not in IMAGE_WIDTH_OPTIONS:
        await query.answer("Unsupported width.", show_alert=True)
        return

    mode = context.user_data.get("selected_mode", "normal")
    image_bytes = context.user_data.get("pending_image")
    if not image_bytes:
        await query.answer("Image expired. Please send it again.", show_alert=True)
        await query.edit_message_text("Image expired. Send a new image.")
        return

    await query.answer()
    context.user_data.pop("pending_image", None)
    context.user_data.pop("selected_mode", None)

    try:
        await query.edit_message_text("Converting image...")
    except TelegramError:
        pass

    # --- conversion ---
    try:
        ascii_art, actual_width, actual_height = make_ascii_art(
            image_bytes, width, mode
        )
        preview = make_preview(ascii_art, actual_width, mode)
        script_file = make_python_file(ascii_art, mode)
        text_file = make_text_file(ascii_art, mode)
    except (WandException, OSError, ValueError):
        logger.exception("Image conversion failed")
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Failed to convert image. Try another image or a lower width.",
            )
        except TelegramError:
            pass
        return
    except Exception:
        logger.exception("Unexpected image conversion error")
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Error generating image files.",
            )
        except TelegramError:
            pass
        return

    # --- upload ---
    chat_id = query.message.chat_id
    mode_names = {"normal": "Normal", "color": "Color", "sharp": "Sharp"}
    sent = 0

    try:
        await send_with_retry(
            context.bot.send_photo,
            chat_id=chat_id,
            photo=preview,
            caption=(
                f"ASCII art - {mode_names[mode]} mode\n"
                f"{actual_width} columns x {actual_height} rows"
            ),
        )
        sent += 1
    except (TimedOut, NetworkError) as error:
        logger.warning("Photo upload failed after retries: %s", error)
    except TelegramError:
        logger.exception("Photo upload rejected by Telegram")

    try:
        await send_with_retry(
            context.bot.send_document,
            chat_id=chat_id,
            document=script_file,
            caption=(
                "Standalone Python script.\n"
                "Run: python ascii_art.py"
            ),
        )
        sent += 1
    except (TimedOut, NetworkError) as error:
        logger.warning("Python upload failed after retries: %s", error)
    except TelegramError:
        logger.exception("Python upload rejected by Telegram")

    try:
        await send_with_retry(
            context.bot.send_document,
            chat_id=chat_id,
            document=text_file,
            caption="Plain text version.",
        )
        sent += 1
    except (TimedOut, NetworkError) as error:
        logger.warning("Text upload failed after retries: %s", error)
    except TelegramError:
        logger.exception("Text upload rejected by Telegram")

    if sent == 0:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "Conversion succeeded, but uploading to Telegram "
                    "timed out. Check your connection and try again."
                ),
            )
        except TelegramError:
            pass


async def render_video_choice(update, context):
    query = update.callback_query
    try:
        parts = query.data.split(":")
        if len(parts) not in (3, 4):
            raise ValueError
        owner_id = int(parts[1])
        width = int(parts[2])
        fps_mode = parts[3] if len(parts) == 4 else "fixed"
    except (ValueError, AttributeError):
        await query.answer("Invalid selection.", show_alert=True)
        return

    if query.from_user.id != owner_id:
        await query.answer("This selection is not yours.", show_alert=True)
        return
    if width not in VIDEO_WIDTH_OPTIONS:
        await query.answer("Unsupported width.", show_alert=True)
        return
    if fps_mode not in ("fixed", "source"):
        await query.answer("Unsupported frame rate.", show_alert=True)
        return

    mode = context.user_data.get("selected_video_mode", "normal")
    video_bytes = context.user_data.get("pending_video")
    if not video_bytes:
        await query.answer("Video expired. Please send it again.", show_alert=True)
        await query.edit_message_text("Video expired. Send a new video.")
        return

    await query.answer()
    context.user_data.pop("pending_video", None)
    context.user_data.pop("selected_video_mode", None)
    context.user_data.pop("selected_video_width", None)

    initial_text = build_progress_text(initial_progress_state())
    status_message = await query.edit_message_text(initial_text)
    chat_id = query.message.chat_id
    progress_queue = asyncio.Queue()
    current_stage = {"value": "validation"}
    progress_task = asyncio.create_task(
        video_progress_updater(
            context.bot, chat_id, status_message.message_id,
            progress_queue, initial_text,
        )
    )
    loop = asyncio.get_running_loop()

    def thread_progress_callback(stage, percent, detail=""):
        current_stage["value"] = stage
        event = {"stage": stage, "percent": percent, "detail": detail}
        try:
            loop.call_soon_threadsafe(progress_queue.put_nowait, event)
        except RuntimeError:
            pass

    try:
        video_output, script_output, actual_fps = await asyncio.to_thread(
            convert_video_to_ascii,
            video_bytes,
            width,
            mode,
            thread_progress_callback,
            fps_mode,
        )

        mode_names = {
            "normal": "Normal", "color": "Color", "sharp": "Sharp",
        }
        fps_label = _format_frame_rate(actual_fps)

        await progress_queue.put({
            "stage": "upload", "percent": 0,
            "detail": "Sending MP4 and Python file",
        })

        video_file = io.BytesIO(video_output)
        video_file.name = "ascii_video.mp4"
        video_file.seek(0)
        await send_with_retry(
            context.bot.send_video,
            chat_id=chat_id,
            video=video_file,
            supports_streaming=True,
            caption=(
                f"ASCII video - {mode_names[mode]} mode\n"
                f"Width: {width} columns\n"
                f"Frame rate: {fps_label} FPS"
            ),
            read_timeout=180,
            write_timeout=180,
            connect_timeout=60,
            pool_timeout=60,
        )

        await progress_queue.put({
            "stage": "upload", "percent": 50,
            "detail": "Sending Python file",
        })

        python_file = io.BytesIO(script_output)
        python_file.name = "ascii_video.py"
        python_file.seek(0)
        await send_with_retry(
            context.bot.send_document,
            chat_id=chat_id,
            document=python_file,
            caption=(
                "Standalone looping ASCII video player.\n\n"
                "Run: python ascii_video.py\n"
                f"Custom FPS: python ascii_video.py --fps {fps_label}\n"
                "No color: python ascii_video.py --no-color\n\n"
                "Requires only Python 3. ANSI-capable terminal for color modes."
            ),
            read_timeout=180,
            write_timeout=180,
            connect_timeout=60,
            pool_timeout=60,
        )

        await progress_queue.put({
            "stage": "upload", "percent": 100,
            "detail": "Files sent",
        })
        await progress_queue.put({"type": "success"})

    except ValueError as error:
        logger.info("Video conversion rejected: %s", error)
        await progress_queue.put({
            "type": "failure",
            "stage": current_stage["value"],
            "message": str(error),
        })
    except Exception as error:
        logger.exception("Video conversion or upload failed")
        await progress_queue.put({
            "type": "failure",
            "stage": current_stage["value"],
            "message": str(error)[:300],
        })
    finally:
        await progress_queue.put({"type": "stop"})
        try:
            await progress_task
        except Exception:
            logger.exception("Progress reporter failed")


async def unknown_message(update, context):
    """Allow natural tool names instead of requiring slash commands."""
    message = update.effective_message
    if message is None or not message.text:
        return

    raw_text = message.text.strip()
    key = " ".join(raw_text.lower().replace("ـ", "").split())

    start_aliases = {"start", "ابدأ", "ابدا", "مساعدة", "help", "lemrens", "menu", "القائمة"}
    cancel_aliases = {"cancel", "إلغاء", "الغاء", "إلغاء العملية", "الغاء العملية", "توقف", "stop"}
    image_aliases = {"image", "images", "photo", "img", "صورة", "الصور", "تحويل صورة", "تحويل الصور", "ascii image", "أداة الصور", "اداة الصور"}
    video_aliases = {"video", "videos", "vid", "فيديو", "الفيديو", "تحويل فيديو", "تحويل الفيديو", "ascii video", "أداة الفيديو", "اداة الفيديو"}

    if key in cancel_aliases:
        await cancel(update, context)
        return
    if key in start_aliases:
        await start(update, context)
        return
    if key in image_aliases:
        context.user_data["preferred_tool"] = "image"
        await message.reply_text(
            "تم تفعيل أداة الصور في Lemrens. أرسل الصورة الآن؛ لا تحتاج إلى كتابة أي أمر."
        )
        return
    if key in video_aliases:
        context.user_data["preferred_tool"] = "video"
        await message.reply_text(
            "تم تفعيل أداة الفيديو في Lemrens. أرسل الفيديو الآن؛ لا تحتاج إلى كتابة أي أمر."
        )
        return

    # Accept mode names as plain text and use them for the pending media item.
    mode_aliases = {
        "normal": "normal", "عادي": "normal", "طبيعي": "normal",
        "color": "color", "colour": "color", "ملون": "color", "ألوان": "color", "الوان": "color",
        "sharp": "sharp", "واضح": "sharp", "حاد": "sharp",
    }
    if key in mode_aliases:
        mode = mode_aliases[key]
        owner_id = message.from_user.id
        if context.user_data.get("pending_image"):
            context.user_data["selected_mode"] = mode
            keyboard = [[
                InlineKeyboardButton(f"منخفض ({IMAGE_WIDTH_OPTIONS[0]})", callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[0]}"),
                InlineKeyboardButton(f"متوسط ({IMAGE_WIDTH_OPTIONS[1]})", callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[1]}"),
                InlineKeyboardButton(f"عالٍ ({IMAGE_WIDTH_OPTIONS[2]})", callback_data=f"ascii:{owner_id}:{IMAGE_WIDTH_OPTIONS[2]}"),
            ]]
            await message.reply_text(
                f"تم اختيار الوضع {mode}. اختر عرض الصورة من الأزرار أدناه:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return
        if context.user_data.get("pending_video"):
            context.user_data["selected_video_mode"] = mode
            keyboard = [[
                InlineKeyboardButton(f"منخفض ({VIDEO_WIDTH_OPTIONS[0]})", callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[0]}"),
                InlineKeyboardButton(f"متوسط ({VIDEO_WIDTH_OPTIONS[1]})", callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[1]}"),
                InlineKeyboardButton(f"عالٍ ({VIDEO_WIDTH_OPTIONS[2]})", callback_data=f"videofps:{owner_id}:{VIDEO_WIDTH_OPTIONS[2]}"),
            ]]
            await message.reply_text(
                f"تم اختيار الوضع {mode}. اختر عرض الفيديو من الأزرار أدناه:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

    await message.reply_text(
        "Lemrens جاهز. اكتب image أو صورة لتفعيل أداة الصور، أو video أو فيديو للفيديو، "
        "أو أرسل الملف مباشرة. للإلغاء اكتب cancel أو إلغاء."
    )


async def error_handler(update, context):
    logger.error("Unhandled Telegram error", exc_info=context.error)


def prompt_token():
    """Read the bot token without echoing it to the terminal."""
    token = os.environ.get("LEMRENS_BOT_TOKEN", "").strip()
    if token:
        return token
    try:
        if sys.stdin.isatty():
            # The animation hides the cursor; show it for the hidden token prompt.
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
            token = getpass(f"{GREEN}أدخل توكن Lemrens (لن يظهر أثناء الكتابة): {RESET}").strip()
        else:
            token = input().strip()
    except (EOFError, KeyboardInterrupt):
        token = ""
    if not token:
        raise SystemExit(f"{RED}لم يتم إدخال التوكن.{RESET}")
    return token


def main():
    banner_state = start_terminal_banner()
    try:
        token = prompt_token()
    except BaseException:
        stop_terminal_banner(banner_state)
        raise

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        stop_terminal_banner(banner_state)
        raise SystemExit(
            "FFmpeg and ffprobe are required. Install with: pkg install ffmpeg"
        )

    application = (
        Application.builder()
        .token(token)
        .connect_timeout(60.0)
        .read_timeout(120.0)
        .write_timeout(120.0)
        .pool_timeout(30.0)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(
        CallbackQueryHandler(choose_mode, pattern=r"^mode:")
    )
    application.add_handler(
        CallbackQueryHandler(render_choice, pattern=r"^ascii:")
    )
    application.add_handler(
        CallbackQueryHandler(choose_video_mode, pattern=r"^video_mode:")
    )
    application.add_handler(
        CallbackQueryHandler(choose_video_fps, pattern=r"^videofps:")
    )
    application.add_handler(
        CallbackQueryHandler(render_video_choice, pattern=r"^videoascii:")
    )

    application.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_image)
    )
    application.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message)
    )

    application.add_error_handler(error_handler)
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        stop_terminal_banner(banner_state)


if __name__ == "__main__":
    main()