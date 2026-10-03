#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace OpenRA.Mods.Cameo.FileSystem
{
	// Locates the player's own C&C Remastered Collection install (Steam) so its HD texture
	// packages can be mounted. Never bundles or redistributes EA assets - reads from the
	// owned install only. Returns nothing (so the game stays vanilla) when not installed.
	public static class RemasterContent
	{
		const string InstallDirName = "CnCRemastered";

		// The HD texture packages mounted when the player opts in. TD + COMMON cover the Tiberian Dawn
		// terrain; RA adds the Red Alert theaters (temperate/snow/interior terrain). Mounted only when
		// the install is present, so absence leaves the game looking exactly like classic.
		public static readonly string[] TexturePackages = { "TEXTURES_TD_SRGB.MEG", "TEXTURES_RA_SRGB.MEG", "TEXTURES_COMMON_SRGB.MEG" };

		// A package that must exist for the install to count as usable.
		const string PrimaryPackage = "TEXTURES_TD_SRGB.MEG";

		static readonly Regex LibraryPathRegex = new("^\\s*\"path\"\\s*\"(?<value>[^\"]*)\"\\s*$");

		// True only when the player has opted in AND a usable install is present. Used to gate
		// both the file system mount and the sprite sequence loader, so a missing install (or an
		// opt-in with the Collection uninstalled) leaves the game looking exactly like classic.
		public static bool IsEnabled()
		{
			var optedIn = Game.Settings?.GetOrCreate<RemasterSettings>(null)?.UseRemasteredArt ?? false;
			return optedIn && TryFindDataDir(out _);
		}

		public static bool TryFindDataDir(out string dataDir)
		{
			dataDir = null;

			foreach (var steamDir in SteamDirectories())
			{
				var candidate = Path.Combine(steamDir, "steamapps", "common", InstallDirName, "Data");
				if (Directory.Exists(candidate) && File.Exists(Path.Combine(candidate, PrimaryPackage)))
				{
					dataDir = candidate;
					return true;
				}
			}

			return false;
		}

		static IEnumerable<string> SteamDirectories()
		{
			var candidatePaths = new List<string>();

			switch (Platform.CurrentPlatform)
			{
				case PlatformType.Windows:
				{
					// Guard the registry access so the analyzer/runtime is satisfied on non-Windows.
					if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
						break;

					var keys = new[]
					{
						(@"HKEY_CURRENT_USER\Software\Valve\Steam", "SteamPath"),
						(@"HKEY_LOCAL_MACHINE\Software\Valve\Steam", "InstallPath"),
						(@"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Valve\Steam", "InstallPath"),
					};

					foreach (var (key, value) in keys)
						if (Registry.GetValue(key, value, null) is string path && !string.IsNullOrEmpty(path))
							candidatePaths.Add(path);

					break;
				}

				case PlatformType.OSX:
					candidatePaths.Add(Path.Combine(
						Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
						"Library", "Application Support", "Steam"));
					break;

				case PlatformType.Linux:
					candidatePaths.Add(Path.Combine(
						Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".steam", "root"));
					candidatePaths.Add(Path.Combine(
						Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
						".var", "app", "com.valvesoftware.Steam", ".steam", "root"));
					break;
			}

			foreach (var libraryPath in candidatePaths.Where(Directory.Exists))
			{
				yield return libraryPath;

				var libraryFoldersPath = Path.Combine(libraryPath, "steamapps", "libraryfolders.vdf");
				if (!File.Exists(libraryFoldersPath))
					continue;

				foreach (var line in File.ReadLines(libraryFoldersPath))
				{
					var match = LibraryPathRegex.Match(line);
					if (match.Success)
						yield return match.Groups["value"].Value.Replace(@"\\", @"\");
				}
			}
		}
	}
}
