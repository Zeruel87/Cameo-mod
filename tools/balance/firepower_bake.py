"""Explicit damage conversion for removing a local unconditional firepower factor.

Pure planning helpers: no YAML or actor mutations. The caller owns weapon-user
closure and must exclude shared-default factors, which were removed separately.
"""
from fractions import Fraction
from math import gcd

from percentage_damage import folded_units
from formula import DAMAGE_STEP

INT32_MAX=2**31-1


def percentage_encoding(ratio, new_flat=None):
    """Smallest practical numerator/denominator for an exact HP fraction.

    Denominator stays a multiple of100, so the engine's final division is by an
    integer. Nested truncations then preserve the positive-damage result.
    If new_flat is provided, also find a Legacy PercentageScale that rounds to
    the chosen numerator. Prefer low numerators to limit intermediate overflow.
    """
    ratio=Fraction(ratio)
    if ratio<0:raise ValueError('negative percentage output is unsupported')
    if ratio==0:return {'units':0,'denominator':10000,'scale':0}
    unit=100//gcd(ratio.denominator,100)
    for multiple in range(1,257):
        numerator=ratio.numerator*unit*multiple
        denominator=ratio.denominator*unit*multiple
        if numerator>INT32_MAX or denominator>INT32_MAX:break
        if new_flat is None:return {'units':numerator,'denominator':denominator}
        if new_flat<=0:raise ValueError('positive folded output cannot follow zero flat damage')
        target=Fraction(numerator*200000,new_flat)
        for scale in {target.numerator//target.denominator,-(-target.numerator//target.denominator)}:
            if 0<scale<=INT32_MAX and folded_units(new_flat,scale)[1]==numerator:
                return {'units':numerator,'denominator':denominator,'scale':scale}
    raise ValueError('no exact bounded integer percentage encoding')


def plan_channel(channel,factor,*,allow_off_grid=False,allow_rounding=False):
    factor=Fraction(factor)
    if factor<0:raise ValueError('negative firepower factor is unsupported')
    kind=channel.value;raw=channel.get('Damage')
    if raw is None:return {'fields':{},'reason':'no Damage field'}
    old=int(raw)
    if kind in {'DamagesConcrete','AffectsIntegrity'}:
        return {'fields':{},'reason':'current engine effect ignores firepower modifiers'}
    if kind=='AreaDamagePercentage':
        denominator=int(channel.get('PercentageDenominator') or 100)
        if denominator%100:raise ValueError('non-integral old percentage division needs review')
        desired=Fraction(old,denominator)*factor
        encoded=percentage_encoding(desired)
        assert Fraction(encoded['units'],encoded['denominator'])==desired
        return {'fields':{'Damage':str(encoded['units']),'PercentageDenominator':str(encoded['denominator'])},
                'percentage_ratio':str(desired),'max_hp_at_unit_modifiers':INT32_MAX*100//max(encoded['units'],1)}
    if kind not in {'AreaDamage','SpreadDamage','TargetDamage'}:
        raise ValueError('unreviewed firepower consumer: '+kind)
    desired=old*factor
    is_chip='extradamage' in channel.key.lower()
    step=1 if allow_off_grid or is_chip else DAMAGE_STEP
    if allow_rounding:
        new=((desired.numerator*2+desired.denominator*step)//(2*desired.denominator*step))*step
    elif desired.denominator!=1:
        if not allow_rounding:raise ValueError('fractional flat damage: '+str(desired))
    else:new=desired.numerator
    if not 0<=new<=INT32_MAX:raise ValueError('flat damage outside supported integer range')
    if new%step:
        raise ValueError(f'main damage outside{step}-grid: '+str(new))
    fields={'Damage':str(new)};proof={'fields':fields,'exact_flat':str(desired),'flat_rounding_error':str(Fraction(new)-desired)}
    scale=int(channel.get('PercentageScale') or 0)
    if kind=='AreaDamage' and scale>0:
        if (channel.get('HeavinessMode') or 'Legacy')!='Legacy':
            raise ValueError('shared heaviness percentage requires separate conversion')
        denominator=int(channel.get('PercentageDenominator') or 10000)
        if denominator%100:raise ValueError('non-integral old folded division needs review')
        before=folded_units(old,scale)[1]
        ratio=Fraction(before,denominator)*factor
        after=folded_units(new,scale)[1]
        if Fraction(after,denominator)!=ratio:
            encoded=percentage_encoding(ratio,new)
            fields['PercentageScale']=str(encoded['scale'])
            fields['PercentageDenominator']=str(encoded['denominator'])
            after=encoded['units'];denominator=encoded['denominator']
        assert Fraction(after,denominator)==ratio
        fields.setdefault('PercentageScale',str(scale))
        fields.setdefault('PercentageDenominator',str(denominator))
        proof.update(percentage_ratio=str(ratio),new_percentage_units=after,
                     max_hp_at_unit_modifiers=INT32_MAX*100//max(after,1))
    return proof
