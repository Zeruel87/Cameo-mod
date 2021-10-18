using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.Player
{
    public class FactionCAInfo : FactionInfo
    {
        [Desc("The game that the faction belongs to.")]
        public readonly string Game = null;
    }
}
