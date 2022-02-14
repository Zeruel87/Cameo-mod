-- Function used for creating waves for a given wave count
WaveGenerator = function(count)
  local e1 = "E1"
  local e2 = "E2"
  local e3 = "E3"
  local e4 = "E4"
  local e6 = "E6"
  local jeep = "RAJEEP"
  local tjeep = "JEEP"
  local bggy = "BGGY"
  local apc = "APC"
  local tnk1 = "1TNK"
  local tnk2 = "2TNK"
  local tnk3 = "3TNK"
  local tnk4 = "4TNK"
  local qtnk = "QTNK"
  local mgg = "RAMGG"
  local ant = "ANT"
  local zm = "ZOMBIE"
  local tnkm = "MTNK"
  local msam = "MSAM"
  local mssm = "MSSM"
  local arty = "ARTY"
  local tnkh = "HTNK"
  local tnkh = "HTNK"
  local dtrk = "DTRK"
  local mh60 = "MTDEMH60"
  local heli = "MTDEHELI"
  local hind = "MTDEHIND"
  local orca = "MTDEORCA"
  local yak = "MTDEYAK"
  local mig = "MTDEMIG"
  local tran = "MTDERATRAN"
  local hip = "MTDEHIP"
  local badger = "MTDEPLA"
  local kirov = "MTDEKIROV"
  local mrj = "MRJ"
  local bike = "BIKE"
  local stnk = "STNK"
  if count == 1 then
    return e1, e1, e1, e1, e1, e1
  elseif count == 2 then
    return e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1
  elseif count == 3 then
    return e1, e1, e1, e1, jeep, jeep, e1, e1, e1, e1
  elseif count == 4 then
    return tnk1, e1, e1, e1, tnk1, e1, e1, e1, tnk1, e1, e1, e1
  elseif count == 5 then
    return tnk2, e1, e1, e1, e1, tnk1, e1, e1, e1, e1, tnk2, e1, e1, e1, e1
  elseif count == 6 then
    return tnk1, tnk1, mgg, e1, e1, e1, e1, e1, e1, tnk2, tnk2, e1, e1, e1, e1
  elseif count == 7 then
    return tnk4, tnk4, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1
  elseif count == 7 then
    return jeep, jeep, tnk1, tnk1, jeep, jeep, tnk2, tnk2
  elseif count == 8 then
    return tnk4, tnk4, mgg, jeep, jeep, jeep, jeep
  elseif count == 9 then
    return tnk3, tnk3, e1, e1, e1, e1, e1, e1, e1, e1, tnk3, tnk3, e1, e1, e1, e1, e1, e1, e1, e1, tnk3, tnk3, e1, e1, e1, e1, e1, e1, e1, e1, jeep, jeep
  elseif count == 10 then
    return tnk4, tnk4, tnk4, tnk4, tnk1, tnk1, tnk1, tnk1, tnk4, tnk4, tnk4, tnk4, tnk2, tnk2, tnk2, tnk2
  elseif count == 11 then
    return mgg, e1, e1, e1, e1, e1, e1, e1, e1, mgg, e1, e1, e1, e1, e1, e1, e1, e1, mgg, tnk4, tnk4, tnk4, tnk4
  elseif count == 12 then
    return mgg, mgg, mgg, mgg, jeep, jeep, jeep, jeep, jeep, jeep, jeep, jeep
  elseif count == 13 then
    return tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1, tnk2, e1, tnk3, e1
  elseif count == 14 then
    return mgg, mgg, mgg, mgg, apc, apc, apc, apc, apc, apc, mgg, mgg, tnk4, tnk4, tnk3, tnk3, mgg, mgg, tnk2, tnk2, tnk2, tnk2
  elseif count == 15 then
    return mgg, mgg, qtnk, qtnk, mgg, mgg, qtnk, qtnk, mgg, mgg, qtnk, qtnk, mgg, mgg, qtnk, qtnk, mgg, mgg
  elseif count == 16 then
    return mgg, mgg, e1, e1, e1, e1, tnk1, tnk1, tnk1, tnk1, mgg, mgg, tnk2, tnk2, mgg, mgg, qtnk, qtnk, tnk4, tnk4, tnk4, tnk4, apc, apc, apc, apc
  elseif count == 17 then
    return tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk1, tnk1, tnk1, tnk1, tnk1, tnk1, tnk1, tnk1
  elseif count == 18 then
    return qtnk, e1, e1, e1, e1, qtnk, e1, e1, e1, e1, qtnk, e1, e1, e1, e1, qtnk, e1, e1, e1, e1, qtnk, e1, e1, e1, e1, mgg, mgg, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1, e1
  elseif count == 19 then
    return qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, mrj, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, mrj, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4, qtnk, tnk4
  elseif count == 20 then
    return e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e4
  elseif count == 21 then
    return e2, e3, e2, e3, e2, e3, e2, e3, e2, e3, e2, e3, e4, e4
  elseif count == 22 then
    return e2, e3, e2, e3, e2, e3, e2, e3, e2, e3, e2, e3, bggy, bggy, bike, e4, e4, e4
  elseif count == 22 then
    return e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, tjeep, tjeep, tjeep, tjeep, bike, bike, e4, e4, e4, e4
  elseif count == 23 then
    return e2, e2, e2, e2, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e4, e4, e4, e4, tjeep, tjeep, tjeep, tjeep, bggy, bggy, bike, bike
  elseif count == 24 then
    return e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e4, e4, tnkm, tnkm, e3, e3, e3, e3, e4, e4, bike, bike
  elseif count == 25 then
    return bggy, bggy, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e4, e4, tnkm, tnkm, e3, e3, e3, e3, bike, bike
  elseif count == 26 then
    return bggy, bggy, tjeep, tjeep, e2, e2, e2, e2, e2, e2, e2, e2, e4, e4, tnkm, tnkm, e3, e3, e3, e3, bike, bike
  elseif count == 27 then
    return bggy, bggy, tjeep, tjeep, e2, e2, e2, e2, e2, e2, e2, e2, e4, e4, tnkm, tnkm, msam, msam, e3, e3, bike, bike
  elseif count == 28 then
    return bggy, bggy, tjeep, tjeep, arty, arty, arty, arty, arty, arty, arty, arty, e4, tnkm, tnkm, msam, msam, e3, e3, bike, bike
  elseif count == 29 then
    return bggy, bggy, tjeep, tjeep, arty, arty, arty, arty, arty, arty, arty, arty, e4, tnkm, tnkm, msam, msam, msam, msam
  elseif count == 30 then
    return bggy, bggy, tjeep, tjeep, arty, arty, arty, arty, arty, arty, arty, arty, e4, tnkm, tnkm, msam, msam, msam, msam
  elseif count == 31 then
    return tnkh, tnkh, tnkh, tnkh, bike, bike, e4, e4, e4, e4, e4, e4
  elseif count == 32 then
    return bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bike, bike, bike, bike, bike, bike, bike, bike, bike, bike, bike
  elseif count == 33 then
    return bggy, arty, bggy, arty, bike, bike, bike, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, arty, bggy, bike, bike, bike
  elseif count == 34 then
    return bggy, bggy, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, tnkh, tnkh, msam, msam, msam, msam, msam, msam, msam, msam, bike, bike, bike
  elseif count == 35 then
    return bggy, bggy, tjeep, tjeep, tjeep, tjeep, tjeep, tjeep, msam, msam, tnkh, tnkh, tnkh, tnkh, msam, msam, msam, msam, msam, msam, msam, msam, bike, bike, bike
  elseif count == 36 then
    return bggy, bggy, msam, msam, msam, msam, msam, msam, msam, msam, tnkh, tnkh, tnkh, tnkh, msam, msam, msam, msam, tnkh, tnkh, tnkh, tnkh, msam, msam, msam, msam, bike, bike, bike
  elseif count == 37 then
    return bggy, bggy, msam, msam, msam, msam, msam, msam, msam, msam, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, msam, msam, msam, msam, bike, bike, bike
  elseif count == 38 then
    return bggy, bggy, msam, msam, msam, msam, msam, msam, msam, msam, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, mssm, msam, msam, msam, msam, bike, bike, bike
  elseif count == 39 then
    return mssm, mssm, msam, msam, msam, msam, msam, msam, msam, msam, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, mssm, msam, msam, msam, msam, bike, bike
  elseif count == 40 then
    return mssm, mssm, mssm, mssm, mssm, bike, bike, mssm, mssm, mssm, mssm, mssm, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, tnkh, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bggy, bike, bike, bggy, bggy, bggy, bggy, msam, msam, msam, msam, bike, bike, bike, bike, bike, bike
  elseif count == 41 then
    return e1, e1, e3, e1, e1, e3, e1, e1, e1, e3, e1, e1, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, mh60, mh60, e4, e4
  elseif count == 42 then
    return e1, e1, e1, e1, e3, e1, e1, e3, e1, e1, e1, e1, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, e2, mh60, mh60, mh60, mh60, e4, e4
  elseif count == 43 then
    return e1, e1, e1, e1, jeep, jeep, mrj, e1, e3, e1, e1, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, jeep, jeep, e1, e3, e1, e1, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, jeep, jeep, e1, e3, e1, e1, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e3, e4, e4, e6, jeep, jeep, mh60, mh60, mh60, mh60, mrj
  elseif count == 44 then
    return tnk1, tnk1, jeep, jeep, mrj, tnk1, tnk1, jeep, jeep, tnk1, tnk1, tnk1, mrj, jeep, jeep, tnk1, tnk1, tnk1, tnk1, mrj, tnk1, jeep, jeep, jeep, jeep, mh60, mh60, mh60, mh60
  elseif count == 45 then
    return tnk2, tnk1, tnk1, mrj, tnk1, tnk1, mrj, tnk1, tnk1, tnk1, mrj, tnk1, tnk1, mrj, tnk2, tnk2, tnk2, tnk2, tnk2, mh60, mh60, mh60, mh60, mh60, mh60
  elseif count == 46 then
    return tnk1, tnk1, tnk1, mrj, tnk1, tnk1, mrj, tnk1, tnk1, mrj, tnk1, tnk1, tnk1, tnk1, mrj, tnk1, tnk1, tnk1, mrj, tnk1, tnk1, tnk1, tnk1, tnk1, tnk1, tnk1, mgg, mh60, mh60, mh60, mh60, heli
  elseif count == 47 then
    return tnk2, mgg, tnk2, mrj, tnk2, tnk2, tnk2, tnk2, mrj, mgg, tnk2, tnk2, tnk2, mrj, tnk2, tnk2, tnk2, mrj, mgg, mh60, mrj, mh60, mh60, mh60, mh60, mh60, heli, heli
  elseif count == 48 then
    return tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk3, tnk3, tnk3, tnk3, tnk3, tnk4, tnk4, tnk4, tnk4, hind, hind, hind, hind, mrj, mrj
  elseif count == 49 then
    return tnk4, tnk3, tnk3, mrj, tnk3, tnk3, mrj, tnk3, tnk3, tnk3, mrj, tnk3, tnk3, tnk4, tnk4, tnk4, tnk4, tnk4, hind, hind, hind, hind, hind, hind, mrj, mrj
  elseif count == 50 then
    return tnk3, tnk3, tnk3, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, mgg, hind, hind, hind, hind, yak
  elseif count == 51 then
    return tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, mrj, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, mgg, hind, hind, hind, hind, yak, yak, tran, tran
  elseif count == 52 then
    return tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, mgg, mrj, yak, yak, yak, yak, yak, yak, tran, tran
  elseif count == 53 then
    return tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, yak, yak, yak, yak, yak, yak, tran, tran
  elseif count == 54 then
    return yak, yak, yak, yak, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, yak, yak, yak, yak, yak, yak, tran, tran
  elseif count == 55 then
    return yak, yak, yak, yak, tnk4, tnk4, tnk4, mrj, tnk4, tnk4, mrj, tnk4, mrj, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, mig, mig, mig, mig, mig, mig, yak, yak, yak, yak, tran, tran
  elseif count == 56 then
    return hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind, hind
  elseif count == 57 then
    return yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, yak, tran, tran, tran, tran
  elseif count == 58 then
    return yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, tran, tran, tran, tran
  elseif count == 59 then
    return dtrk, e4, e4, e4, e4, mrj, e2, e2, e2, mrj, e2, e2, e2, e2, e2, hind, hind, hind, hind, e2, e2, e2, e2, yak, yak, yak, yak, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, yak, yak, yak, yak, yak, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, tran, tran, tran, tran
  elseif count == 60 then
    return dtrk, dtrk, e2, mrj, e4, e4, e4, e4, e4, e2, e2, mrj, e2, e2, e2, hind, hind, hind, hind, e2, e2, e2, e2, yak, yak, yak, yak, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, yak, yak, yak, yak, yak, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, dtrk, e2, e2, e2, e2, e2, e2, e2, e2, e2, e4, e4, e4, dtrk, hind, hind, hind, hind, e4, e4, e4, e4, yak, yak, yak, yak, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, tnk4, qtnk, qtnk, qtnk, qtnk, yak, yak, yak, yak, yak, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, yak, mig, tran, tran, tran, tran, e6, e6
 elseif count == 61 then
    return hip, tnk4, hip, tnk4, hip, tnk4, hip, tnk4, tnk4, hip, tnk4, tnk4, hip, tnk4, tnk4, hip, tnk4, tnk4, hip, tnk4, tnk4, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, dtrk, dtrk, mig, dtrk, dtrk, hip, hip, hip, mig, dtrk, dtrk, mig, dtrk, dtrk, mig, dtrk, dtrk, mig, dtrk, mig, dtrk, dtrk, mig, mig, mig, mig, hip, hip, hip
 elseif count == 62 then
    return hip, badger, hip, badger, hip, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, badger, badger, mig, badger, badger, hip, hip, hip, mig, badger, badger, mig, badger, badger, mig, badger, badger, mig, badger, mig, badger, badger, mig, mig, mig, mig, hip, hip, hip
  elseif count == 63 then
    return kirov, badger, hip, badger, hip, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, kirov, kirov, kirov, kirov, kirov, hip, hip, hip, kirov, kirov, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, mig, mig, mig, kirov, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, badger, badger, mig, badger, badger, kirov, kirov, hip, mig, badger, badger, mig, badger, badger, mig, badger, badger, mig, badger, mig, badger, badger, mig, mig, mig, mig, hip, hip, hip
  elseif count == 64 then
    return kirov, badger, hip, badger, hip, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, badger, badger, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, kirov, kirov, kirov, kirov, kirov, hip, kirov, hip, kirov, kirov, kirov, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, kirov, kirov, kirov, kirov, kirov, hip, mig, mig, mig, kirov, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, badger, badger, mig, badger, badger, kirov, kirov, hip, mig, badger, badger, mig, badger, badger, mig, badger, badger, mig, badger, mig, badger, badger, mig, mig, mig, mig, kirov, hip, kirov
  elseif count == 65 then
    return kirov, badger, hip, badger, hip, badger, hip, badger, badger, badger, badger, badger, badger, badger, badger, hip, badger, badger, hip, badger, badger, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, kirov, kirov, kirov, kirov, kirov, hip, kirov, badger, kirov, kirov, kirov, badger, badger, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, hip, kirov, kirov, kirov, kirov, kirov, badger, mig, mig, mig, kirov, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, mig, badger, badger, kirov, badger, kirov, badger, mig, badger, mig, badger, mig, mig, badger, badger, mig, badger, badger, kirov, kirov, hip, mig, badger, badger, mig, badger, badger, mig, badger, badger, mig, badger, mig, badger, badger, mig, mig, mig, mig, kirov, kirov, kirov
  elseif count == 66 then
    return e6, mrj, e6, e6, e6, e6, orca, e6, e6, mrj, e6, e6, orca, e6, e6, mrj, e6, e6, orca, e6, e6, mrj, e6, e6, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, e6, e6, e6, e6, e6, orca, e6, e6, e6, e6, orca, e6, e6, e6, e6, orca, e6, e6, e6, e6, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca
  elseif count == 67 then
    return tjeep, mrj, tjeep, tjeep, tjeep, tjeep, orca, apc, apc, mrj, apc, apc, orca, tnkm, tnkm, mrj, tnkm, tnkm, orca, msam, msam, mrj, msam, msam, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, tjeep, tjeep, tjeep, tjeep, tjeep, orca, apc, apc, apc, apc, orca, tnkm, tnkm, tnkm, tnkm, orca, msam, msam, msam, msam, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, tnkh, tnkh, tnkh, tnkh, orca, tnkh, tnkh, tnkh, tnkh, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca, orca
  elseif count == 68 then
    return mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj, mrj
  elseif count == 69 then
    return mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh, mrj, tnkh
  elseif count == 70 then
    return mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, mrj, tnkh, orca, stnk
  elseif count == 71 then
    return mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, mrj, tnkh, stnk, stnk, stnk, stnk, stnk, stnk, stnk
  elseif count == 72 then
    return ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant, ant
  end
end

GivePlayerMoney = function()
	Trigger.AfterDelay(1, function()
		moneyMakers = Map.ActorsInBox(Map.TopLeft, Map.BottomRight, function(actor) return actor.Type == "tower.money" end)
		for i, v in ipairs(moneyMakers) do
			MTD.GiveCash(60)
			Media.FloatingText("$60", WPos.New(v.CenterPosition.X, v.CenterPosition.Y, v.CenterPosition.Z), 30, HSLColor.Green)
		end
	end)
end


WaveEndCallback = function(count)
  GivePlayerMoney()
  MTD.GiveCash(200 + math.floor(count / 5) * 100 + math.floor(count / 10) * 100 + math.floor(count / 15) * 100)
  Media.DisplayMessage(string.format("Wave %d completed", count))
end

WorldLoaded = function()
  local player = Player.GetPlayer("Multi0")
  local enemy = Player.GetPlayer("Creeps")
  MTD.SetPlayer(player)
  MTD.SetEnemy(enemy)
  MTD.SetWaveGen(WaveGenerator)
  MTD.SetOnExitWaveMode(WaveEndCallback)
  MTD.Begin()
end
