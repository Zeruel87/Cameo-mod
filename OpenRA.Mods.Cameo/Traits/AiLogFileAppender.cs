#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace OpenRA.Mods.Cameo.Traits
{
	internal enum AiLogAppendResult { Appended, RetryableFailure, Failed }

	internal sealed class AiLogFileAppender
	{
		readonly string filePath;
		readonly string mutexName;
		int attempts;

		public bool IsTerminal { get; private set; }

		public AiLogFileAppender(string fileName)
		{
			filePath = Path.Combine(Platform.SupportDir, "Logs", fileName);
			var canonicalPath = Path.GetFullPath(filePath);
			if (OperatingSystem.IsWindows())
				canonicalPath = canonicalPath.ToUpperInvariant();

			mutexName = "OpenRA-CameoAiLog-" + Convert.ToHexString(
				SHA256.HashData(Encoding.UTF8.GetBytes(canonicalPath)));
		}

		public AiLogAppendResult TryAppend(string text, int worldTick, out int nextAttemptTick)
		{
			attempts++;
			var result = Append(text);
			if (result != AiLogAppendResult.RetryableFailure || attempts >= 8)
			{
				IsTerminal = true;
				nextAttemptTick = worldTick;
				return result;
			}

			nextAttemptTick = worldTick + Math.Min(1 << Math.Min(attempts - 1, 5), 30);
			return result;
		}

		AiLogAppendResult Append(string text)
		{
			Mutex mutex = null;
			try
			{
				mutex = new Mutex(false, mutexName);
				try
				{
					if (!mutex.WaitOne(TimeSpan.FromMilliseconds(100)))
						return AiLogAppendResult.RetryableFailure;
				}
				catch (AbandonedMutexException) { }

				try
				{
					Directory.CreateDirectory(Path.GetDirectoryName(filePath));
					File.AppendAllText(filePath, text, new UTF8Encoding(false));
					return AiLogAppendResult.Appended;
				}
				catch { return AiLogAppendResult.Failed; }
				finally
				{
					try { mutex.ReleaseMutex(); }
					catch { }
				}
			}
			catch { return AiLogAppendResult.Failed; }
			finally { mutex?.Dispose(); }
		}
	}
}
