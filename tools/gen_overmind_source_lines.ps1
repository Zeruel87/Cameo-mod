# Generate SOURCE WAVs for the missing Zerg notification lines using Windows TTS
# (SAPI) with SSML prosody, so each line carries an intended *energy* (the
# Overmind timbre is applied later by the RVC model; only delivery comes from here).
#
# These are the SOURCE for RVC conversion at transpose 0 (David is already low).
# Output -> docs/overmind-voice/src_lines/  (tools/ holds scripts only).
#
# Edit a line's text or energy below and re-run to regenerate.
#   pwsh tools/gen_overmind_source_lines.ps1
#
# energy levels: ominous | calm | neutral | alert | urgent

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$outDir = Join-Path $repo "docs\overmind-voice\src_lines"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# token -> { text ; energy }. watk/wsign skipped (Dune sandworm, irrelevant to Zerg).
$lines = [ordered]@{
    "abldgin1" = @{ text = "Building.";                    energy = "neutral" }
    "abldgin2" = @{ text = "Construction underway.";       energy = "neutral" }
    "conscmp1" = @{ text = "Construction complete.";       energy = "neutral" }
    "conscmp2" = @{ text = "Structure complete.";          energy = "neutral" }
    "unitrdy1" = @{ text = "Unit ready.";                  energy = "alert"   }
    "train1"   = @{ text = "Spawning.";                    energy = "neutral" }
    "upg"      = @{ text = "Evolving.";                    energy = "neutral" }
    "repair1"  = @{ text = "Regenerating.";                energy = "neutral" }
    "cancld1"  = @{ text = "Cancelled.";                   energy = "calm"    }
    "onhold1"  = @{ text = "On hold.";                     energy = "calm"    }
    "newopt1"  = @{ text = "New strains available.";       energy = "alert"   }
    "pribldg1" = @{ text = "Primary structure selected.";  energy = "neutral" }
    "select1"  = @{ text = "Select target.";               energy = "alert"   }
    "nodeply1" = @{ text = "Cannot spawn here.";           energy = "neutral" }
    "nodeply2" = @{ text = "Unsuitable ground.";           energy = "neutral" }
    "silond1"  = @{ text = "More storage required.";       energy = "alert"   }
    "reinfor1" = @{ text = "The swarm arrives.";           energy = "urgent"  }
    "strucap1" = @{ text = "Structure assimilated.";       energy = "alert"   }
    "strclst1" = @{ text = "Structure lost.";              energy = "alert"   }
    "unitlst1" = @{ text = "A minion has fallen.";         energy = "ominous" }
    "aunitl1"  = @{ text = "Flyer lost.";                  energy = "alert"   }
    "unitrep1" = @{ text = "Regeneration complete.";       energy = "neutral" }
    "unitsld1" = @{ text = "Reclaimed.";                   energy = "neutral" }
    "aready1"  = @{ text = "The weapon is ready.";         energy = "urgent"  }
    "dhrdy"    = @{ text = "The weapon is ready.";         energy = "urgent"  }
    "dhchg"    = @{ text = "The weapon gathers strength."; energy = "ominous" }
    "misnwon1" = @{ text = "We are victorious.";           energy = "urgent"  }
    "fail1"    = @{ text = "The swarm is broken.";         energy = "ominous" }
    "save1"    = @{ text = "Progress preserved.";          energy = "calm"    }
    "load1"    = @{ text = "Resuming.";                    energy = "calm"    }
}

# energy -> SAPI SSML prosody. Kept moderate; extreme prosody makes RVC artifact.
$profiles = @{
    "ominous" = @{ rate = "x-slow"; pitch = "low";    emph = "none"     }
    "calm"    = @{ rate = "slow";   pitch = "low";    emph = "none"     }
    "neutral" = @{ rate = "medium"; pitch = "medium"; emph = "none"     }
    "alert"   = @{ rate = "fast";   pitch = "high";   emph = "moderate" }
    "urgent"  = @{ rate = "fast";   pitch = "high";   emph = "strong"   }
}

function Escape-Xml([string]$s) {
    return $s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
}

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice("Microsoft David Desktop")   # male, low register -> RVC transpose 0
$synth.Volume = 100

$n = 0
foreach ($token in $lines.Keys) {
    $text = $lines[$token].text
    $energy = $lines[$token].energy
    $p = $profiles[$energy]
    $body = Escape-Xml $text
    $ssml = @"
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<prosody rate="$($p.rate)" pitch="$($p.pitch)"><emphasis level="$($p.emph)">$body</emphasis></prosody>
</speak>
"@
    $path = Join-Path $outDir ("scz_{0}.wav" -f $token)
    $synth.SetOutputToWaveFile($path)
    $synth.SpeakSsml($ssml)
    $n++
    Write-Output ("[{0,2}/{1}] scz_{2}.wav  [{3,-7}] <- `"{4}`"" -f $n, $lines.Count, $token, $energy, $text)
}
$synth.SetOutputToNull()
$synth.Dispose()
Write-Output ""
Write-Output ("Done. {0} source clips in {1}" -f $lines.Count, $outDir)
