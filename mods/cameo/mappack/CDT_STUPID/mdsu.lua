MDSU = {}

MDSU.Dict = {}
local Dict = MDSU.Dict

MDSU.List = {}
local List = MDSU.List

MDSU.Set = MDSU.Set or {}
local Set = MDSU.Set

MDSU.Tuple = {}
local Tuple = MDSU.Tuple

Dict.New = function(...)

  local dict = {}
  dict._size = 0
  dict._values = {}
  dict._eval = function() end
  dict._copy = function(d)
    local values = {}
    for k, v in pairs(dict._values) do
      values[k] = v
    end
    d._values = values
    d._size = dict._size
  end

  dict.Contains = function(k)
    dict.Eval()
    return dict._values[k] ~= nil
  end

  dict.Copy = function()
    local copy = Dict.New()
    copy._size = dict._size
    copy._eval = function(d)
      dict._copy(d)
      dict._eval(d)
    end
    copy._copy = dict._copy
    return dict
  end

  dict.Equals = function(d)
    dict.Eval()
    d.Eval()
    if dict._size ~= m._size then
      return false
    end
    
    for k, v in pairs(dict._values) do
      if d._values[k] ~= v then
        return false
      end
    end

    return true
  end

  dict.Eval = function()
    dict._eval(dict)
    dict._copy = function(d)
      local values = {}
      for k, v in pairs(dict._values) do
        values[k] = v
      end
      d._values = values
      d._size = dict._size
    end
    dict._eval = function() end
  end

  dict.Exists = function(p)
    dict.Eval()
    for k, v in dict.Iterator() do
      if p(k, v) then
        return true
      end
    end
    return false
  end

  dict.Filter = function(p)
    local filtered = Dict.New()
    filtered._eval = function(d)
      dict.Eval()
      for k, v in dict.Iterator() do
        if p(k, v) then
          filtered._values[k] = v
          filtered._size = filtered._size + 1
        end
      end
    end
    return filtered
  end

  dict.FilterNot = function(p)
    return dict.Filter(function(k, v) return not p(k, v) end)
  end

  dict.Fold = function(w, f)
    dict.Eval()
    for k, v in dict.Iterator() do
      w = f(w, Tuple.New(k, v))
    end
    return w
  end

  dict.ForAll = function(p)
    dict.Eval()
    for k, v in dict.Iterator() do
      if not p(k, v) then
        return false
      end
    end
    return true
  end

  dict.ForEach = function(f)
    dict.Eval()
    for k, v in dict.Iterator() do
      f(k, v)
    end
  end

  dict.Get = function(k)
    dict.Eval()
    return dict._values[k]
  end

  dict.GetOrElse = function(k, v)
    dict.Eval()
    if dict._values[k] ~= nil then
      return dict._values[k]
    end
    return v
  end

  dict.IsDefinedAt = function(k)
    dict.Eval()
    return dict._values[k] ~= nil
  end

  dict.IsEmpty = function()
    dict.Eval()
    return dict._size == 0
  end

  dict.Iterator = function()
    dict.Eval()
    local k, v
    return function()
      k, v = next(dict._values, k)
      if k ~= nil then
        return k, v
      end
    end
  end

  dict.KeySet = function()
    return Set.New(dict.Keys())
  end

  dict.Keys = function()
    dict.Eval()
    local it = dict.Iterator()
    local f
    f = function()
      local k, v = it()
      if k then
        return k, f()
      end
    end
    return f()
  end

  dict.KeysIterator = function()
    local it = dict.Iterator()
    local f = function()
      local k, v = it()
      if k then
        return k
      end
    end
  end

  dict.MaxBy = function(f)
    dict.Eval()
    local mK, mV = nil, nil
    for k, v in dict.Iterator() do
      if not mK or f(k, v) > f(mK, mV) then
        mK, mV = k, v
      end
    end
    return mK, mV
  end

  dict.MinBy = function(f)
    dict.Eval()
    local mK, mV = nil, nil
    for k, v in dict.Iterator() do
      if not mK or f(k, v) < f(mK, mV) then
        mK, mV = k, v
      end
    end
    return mK, mV
  end

  dict.NonEmpty = function()
    dict.Eval()
    return dict._size > 0
  end

  dict.Removed = function(k)
    local copy = dict.Copy()
    local prevEval = copy._eval
    copy._eval = function(d)
      prevEval(d)
      if d._values[k] ~= nil then
        d._values[k] = nil
        d._size = d._size - 1
      end
    end
    return copy
  end

  dict.Size = function()
    dict.Eval()
    return dict._size
  end

  dict.ToString = function()
    dict.Eval()
    local s = '{'
    local d = ''
    for k, v in dict.Iterator() do
      s = s .. d .. tostring(k) .. ' -> ' .. tostring(v)
      d = ', '
    end
    s = s .. '}'
    return s
  end

  dict.Unpack = function()
    dict.Eval()
    local it = dict.Iterator()
    local f
    f = function()
      local k, v = it()
      if k then
        return Tuple.New(k, v), f()
      end
    end
    return f()
  end

  dict.Values = function()
    dict.Eval()
    local it = dict.Iterator()
    local f
    f = function()
      local k, v = it()
      if k then
        return v, f()
      end
    end
    return f()
  end

  dict.ValuesIterator = function()
    dict.Eval()
    local it = dict.Iterator()
    local f = function()
      local k, v = it()
      if k then
        return v
      end
    end
    return f
  end

  dict.Updated = function(k, v)
    local copy = dict.Copy()
    local prevEval = dict._eval
    copy._eval = function(d)
      prevEval(d)
      if d._values[k] == nil then
        d._size = d._size + 1
      end
      d._values[k] = v
    end
    return copy
  end

  for _, t in ipairs(arg) do
    local k, v = t.Unpack()
    if dict._values[k] == nil then
      dict._values[k] = v
      dict._size = dict._size + 1
    end
  end

  return dict
end

List.New = function(...)
  local list = {}
  list._size = 0
  list._values = {}
  list._eval = function() end
  list._copy = function(l)
    local values = {}
    for i = 0, list._size - 1 do
      values[i] = list._values[i]
    end
    l._values = values
    l._size = list._size
  end

  list.Appended = function(...)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      for _, v in ipairs(arg) do
        l._values[l._size] = v
        l._size = l._size + 1
      end
    end
    return copy
  end

  list.Contains = function(w)
    list.Eval()
    for _, v in list.Iterator() do
      if v == w then
        return true
      end
    end
    return false
  end

  list.Copy = function()
    local copy = List.New()
    copy._size = list._size
    copy._eval = function(l)
      list._copy(l)
      list._eval(l)
    end
    copy._copy = list._copy
    return copy
  end

  list.Drop = function(n)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      for i = n, l._size - 1 do
        l._values[i - n] = l._values[i]
        l._values[i] = nil
      end
      l._size = l._size - n
    end
    return copy
  end

  list.DropRight = function(n)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      for i = 0, n - 1 do
        l._size = l._size - 1
        l._values[l._size] = nil
      end
    end
    return copy
  end

  list.DropWhile = function(p)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local n = 0
      for i = 0, l._size - 1 do
        local v = l._values[i]
        if p(v) then
          n = n + 1
        else
          break
        end
      end
      for i = n, l._size - 1 do
        l._values[i - n] = l._values[i]
        l._values[i] = nil
      end
      l._size = l._size - n
    end
    return copy
  end

  list.Equals = function(l)
    list.Eval()
    l.Eval()
    if list._size ~= l._size then
      return false
    end
    for i, v in list.Iterator() do
      if l._values[i] ~= v then
        return false
      end
    end
    return true
  end

  list.Eval = function()
    list._eval(list)
    list._copy = function(l)
      local values = {}
      for i = 0, list._size - 1 do
        values[i] = list._values[i]
      end
      l._values = values
      l._size = list._size
    end
    list._eval = function() end
  end

  list.Exists = function(p)
    list.Eval()
    for _, v in list.Iterator() do
      if p(v) then
        return true
      end
    end
    return false
  end

  list.Filter = function(p)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local values = {}
      l._size = 0
      for i = 0, list._size - 1 do
        local v = list._values[i]
        if p(v) then
          values[l._size] = v
          l._size = l._size + 1
        end
      end
      l._values = values
    end
    return copy
  end

  list.FilterNot = function(p)
    return list.Filter(function(v) return not p(v) end)
  end

  list.Find = function(p)
    list.Eval()
    for _, v in list.Iterator() do
      if p(v) then
        return v
      end
    end
  end

  list.Fold = function(w, f)
    list.Eval()
    return list.FoldLeft(w, f)
  end

  list.FoldLeft = function(w, f)
    list.Eval()
    for _, v in list.Iterator() do
      w = f(w, v)
    end
    return w
  end

  list.FoldRight = function(w, f)
    list.Eval()
    for _, v in list.ReverseIterator() do
      w = f(w, v)
    end
    return w
  end

  list.ForAll = function(p)
    list.Eval()
    for _, v in list.Iterator() do
      if not p(v) then
        return false
      end
    end
    return true
  end

  list.ForEach = function(f)
    list.Eval()
    for _, v in list.Iterator() do
      f(v)
    end
  end

  list.Get = function(i)
    list.Eval()
    return list._values[i]
  end

  list.GetOrElse = function(i, v)
    list.Eval()
    if list._size > i and i >= 0 then
      return list._values[i]
    end
    return v
  end

  list.Head = function()
    list.Eval()
    assert(list._size > 0, "LIST ASSERT FAILED")
    return list._values[0]
  end

  list.IndexOf = function(w)
    list.Eval()
    for i, v in list.Iterator() do
      if v == w then
        return i
      end
    end
  end

  list.IndexWhere = function(p)
    list.Eval()
    for i, v in list.Iterator() do
      if p(v) then
        return i
      end
    end
  end

  list.Indices = function()
    list.Eval()
    local indices = List.New()
    for i = 0, list._size - 1 do
      indices._values[i] = i
    end
    return newList
  end

  list.Init = function()
    local copy = List.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      l._values[l._size - 1] = nil
      l._size = l._size - 1
    end
    return copy
  end

  list.IsDefinedAt = function(i)
    list.Eval()
    return list._size > i and i >= 0
  end
  
  list.IsEmpty = function()
    list.Eval()
    return list._size == 0
  end

  list.Iterator = function()
    list.Eval()
    local i = -1
    return function()
      i = i + 1
      if i < list._size then
        return i, list._values[i]
      end
    end
  end

  list.Last = function()
    list.Eval()
    return list._values[list._size - 1]
  end

  list.LastIndexOf = function(w)
    list.Eval()
    for i = list._size - 1, 0 do
      if list._values[i] == w then
        return i
      end
    end
  end

  list.LastIndexWhere = function(p)
    list.Eval()
    for i = list._size - 1, 0 do
      if p(list._values[i]) then
        return i
      end
    end
  end

  list.Map = function(f)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local values = {}
      for i = 0, list._size - 1 do
        values[i] = f(list._values[i])
      end
      copy._values = values
    end
    return copy
  end

  list.Max = function()
    list.Eval()
    local w = nil
    for _, v in list.Iterator() do
      if not w or v > w then
        w = v
      end
    end
    return w
  end

  list.MaxBy = function(f)
    list.Eval()
    local w = nil
    for _, v in list.Iterator do
      if not w or f(v) > f(w) then
        w = v
      end
    end
    return w
  end

  list.Min = function()
    list.Eval()
    local w = nil
    for _, v in list.Iterator() do
      if not w or v < w then
        w = v
      end
    end
    return w
  end

  list.MinBy = function(f)
    list.Eval()
    local w = nil
    for _, v in list.Iterator() do
      if not w or f(v) < f(w) then
        w = v
      end
    end
    return w
  end

  list.NonEmpty = function()
    list.Eval()
    return list._size > 0
  end

  list.PadTo = function(n, v)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      while l._size < n do
        l._values[l._size] = v
        l._size = l._size + 1
      end
    end
    return copy
  end

  list.Partition = function(p)
    return list.Filter(p), list.FilterNot(p)
  end

  list.Prepended = function(...)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local n = #arg
      for i = l._size - 1, 0 do
        l._values[i + n] = l._values[i]
      end
      for i, v in ipairs(arg) do
        l._values[i - 1] = v
      end
      l._size = l._size + n
    end
    return copy
  end

  list.Product = function()
    return list.Fold(1, function(v, w) return v * w end)
  end

  list.Reverse = function()
    local copy = List.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local values = {}
      for i = 0, l._size - 1 do
        values[l._size - i - 1] = l._values[i]
      end
    end
    return copy
  end

  list.ReverseIterator = function()
    list.Eval()
    local i = list._size
    local f = function()
      if i > 0 then
        i = i - 1
        return i, list._values[i]
      end
    end
    return f
  end

  list.Size = function()
    list.Eval()
    return list._size
  end

  list.Slice = function(i, j)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local values = {}
      l._size = 0
      for i = i, j do
        values[l._size] = l._values[i]
        l._size = l._size + 1
      end
    end
    return copy
  end

  list.SortBy = function(f)
    -- TODO
    return list.Copy()
  end

  list.Sorted = function()
    return list.SortBy(function(v, w) return v < w end)
  end

  list.SplitAt = function(i)
    return list.Take(i), list.Drop(i)
  end

  list.Sum = function()
    return list.Fold(0, function(v, w) return v + w end)
  end

  list.Tail = function()
    return list.Drop(1)
  end

  list.Take = function(n)
    return list.DropRight(list._size - n)
  end

  list.TakeRight = function(n)
    return list.Drop(list._size - n)
  end

  list.TakeWhile = function(p)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      local values = {}
      l._size = 0
      for i = 0, l._size - 1 do
        local v = l._values[i]
        if p(v) then
          values[i] = v
        else
          l._size = i
          break
        end
      end
      l._values = values
    end
    return copy
  end

  list.ToList = function()
    list.Eval()
    return list.Copy(list.Unpack())
  end

  list.ToSet = function()
    list.Eval()
    return Set.New(list.Unpack())
  end

  list.ToString = function()
    list.Eval()
    local s = '['
    local d = ''
    list.ForEach(function(v) s = s .. d .. tostring(v) d = ', ' end)
    s = s .. ']'
    return s
  end

  list.ToTuple = function()
    list.Eval()
    return Tuple.New(list.Unpack())
  end

  list.Unpack = function()
    list.Eval()
    local it = list.Iterator()
    local f
    f = function()
      local _, v = it()
      if v ~= nil then
        return v, f()
      end
    end
    return f()
  end

  list.Unzip = function()
    return list.Map(function(v) return v.Get(0) end), list.Map(function(v) return v.Get(1) end)
  end

  list.Updated = function(i, v)
    local copy = list.Copy()
    local prevEval = copy._eval
    copy._eval = function(l)
      prevEval(l)
      if i >= l._size then
        l._size = i + 1
      end
      l._values[i] = v
    end
    return copy
  end

  list.Zip = function(l0)
    local zipped = list.New()
    zipped._eval = function(l1)
      l0.Eval()
      list.Eval()
      local n = math.min(l0._size, list._size)
      for i = 0, n - 1 do
        l1._values[i] = Tuple.New(list._values[i], l0._values[i])
      end
      l1._size = n
    end
    return zipped
  end

  list.ZipWithIndex = function()
    local zipped = List.New()
    zipped._eval = function(l)
      for i, v in list.Iterator() do
        zipped._values[i] = Tuple.New(i, v)
      end
      zipped._size = list._size
    end
  end

  for _, v in ipairs(arg) do
    list._values[list._size] = v
    list._size = list._size + 1
  end

  return list
end

Set.New = function(...)
  local set = {}
  set._size = 0
  set._values = {}
  set._eval = function() end
  set._copy = function(s)
    local values = {}
    for v in pairs(set._values) do
      values[v] = true
    end
    s._values = values
    s._size = set._size
  end

  set.Contains = function(v)
    set.Eval()
    return set._values[v] ~= nil
  end

  set.Copy = function()
    local copy = Set.New()
    copy._size = set._size
    copy._eval = function(s)
      set._copy(s)
      set._eval(s)
    end
    copy._copy = set._copy
    return copy
  end
  
  set.Difference = function(s)
    return set.FilterNot(function(v) return s.Contains(v) end)
  end
  
  set.Equals = function(s)
    set.Eval()
    s.Eval()
    return set._size == s._size
       and set.ForAll(function(v) return s.Contains(v) end)
  end

  set.Eval = function()
    set._eval(set)
    set._copy = function(s)
      local values = {}
      for v in pairs(set._values) do
        values[v] = true
      end
      s._values = values
      s._size = set._size
    end
    set._eval = function() end
  end

  set.Excl = function(...)
    local copy = set.Copy()
    local prevEval = copy._eval
    copy._eval = function(s)
      prevEval(s)
      for _, v in ipairs(arg) do
        if s._values[v] then
          s._values[v] = nil
          s._size = s._size - 1
        end
      end
    end
    return copy
  end

  set.Exists = function(p)
    set.Eval()
    for v in set.Iterator() do
      if p(v) then
        return true
      end
    end
    return false
  end

  set.Filter = function(p)
    local copy = set.Copy()
    local prevEval = copy._eval
    copy._eval = function(s)
      prevEval(s)
      local values = {}
      s._size = 0
      for v in pairs(s._values) do
        if p(v) then
          values[v] = true
          s._size = s._size + 1
        end
      end
      s._values = values
    end
    return copy
  end

  set.FilterNot = function(p)
    return set.Filter(function(v) return not p(v) end)
  end

  set.Find = function(p)
    set.Eval()
    for v in set.Iterator() do
      if p(v) then
        return v
      end
    end
  end

  set.Fold = function(w, f)
    set.Eval()
    for v in set.Iterator() do
      w = f(w, v)
    end
    return w
  end

  set.ForAll = function(p)
    set.Eval()
    for v in set.Iterator() do
      if not p(v) then
        return false
      end
    end
    return true
  end

  set.ForEach = function(f)
    set.Eval()
    for v in set.Iterator() do
      f(v)
    end
  end

  set.Incl = function(...)
    local copy = set.Copy()
    local prevEval = copy._eval
    copy._eval = function(s)
      prevEval(s)
      for _, v in ipairs(arg) do
        if not s._values[v] then
          s._values[v] = true
          s._size = s._size + 1
        end
      end
    end
    return copy
  end

  set.Intersect = function(s)
    return set.Filter(function(v) return s.Contains(v) end)
  end
  
  set.IsEmpty = function()
    set.Eval()
    return set._size == 0
  end

  set.Iterator = function()
    set.Eval()
    local v
    return function()
      v = next(set._values, v)
      if v ~= nil then
        return v
      end
    end
  end

  set.Map = function(f)
    local copy = set.Copy()
    local prevEval = copy._eval
    copy._eval = function(s)
      prevEval(s)
      local values = {}
      for v in pairs(s._values) do
        values[f(v)] = true
      end
      s._values = values
    end
    return copy
  end

  set.Max = function()
    set.Eval()
    local max = nil
    for v in set.Iterator() do
      if not max or max < v then
        max = v
      end
    end
    return max
  end

  set.MaxBy = function(f)
    set.Eval()
    local max = nil
    for v in set.Iterator() do
      if not max or f(max) < f(v) then
        max = v
      end
    end
    return max
  end

  set.Min = function()
    set.Eval()
    local min = nil
    for v in set.Iterator() do
      if not min or min > v then
        min = v
      end
    end
    return min
  end

  set.MinBy = function(f)
    set.Eval()
    local min = nil
    for v in set.Iterator() do
      if not min or f(min) > f(v) then
        min = v
      end
    end
    return min
  end

  set.NonEmpty = function()
    set.Eval()
    return set._size > 0
  end

  set.Partition = function(p)
    return set.Filter(p), set.FilterNot(p)
  end

  set.Product = function()
    return set.Fold(1, function(x, y) return x * y end)
  end

  set.Size = function()
    set.Eval()
    return set._size
  end

  set.SubsetOf = function(s)
    set.Eval()
    return s.ForAll(function(v) s.Contains(v) end)
  end

  set.Sum = function()
    return set.Fold(0, function(x, y) return x + y end)
  end

  set.ToList = function()
    return List.New(set.Unpack)
  end

  set.ToSet = function()
    return set.Copy()
  end

  set.ToString = function()
    set.Eval()
    local s = '{'
    local d = ''
    for v in set.Iterator() do
      s = s .. d .. tostring(v)
      d = ', '
    end
    s = s .. '}'
    return s
  end

  set.ToTuple = function()
    return Tuple.New(set.Unpack())
  end

  set.Union = function(s)
    return set.Incl(s.Unpack())
  end

  set.Unpack = function()
    set.Eval()
    local it = set.Iterator()
    local f
    f = function()
      local v = it()
      if v then
        return v, f()
      end
    end
    return f()
  end

  for _, v in ipairs(arg) do
    if set._values[v] == nil then
      set._values[v] = true
      set._size = set._size + 1
    end
  end

  return set
end

Tuple.New = function(...)

  local tuple = {}
  tuple._size = 0
  tuple._values = {}
  tuple._eval = function() end
  tuple._copy = function(t)
    local values = {}
    for i = 0, tuple._size - 1 do
      values[i] = tuple._values[i]
    end
    t._values = values
    t._size = tuple._size
  end

  tuple.Contains = function(w)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      if v == w then
        return true
      end
    end
    return false
  end

  tuple.Copy = function()
    local copy = Tuple.New()
    copy._size = tuple._size
    copy._eval = function(t)
      tuple._copy(t)
      tuple._eval(t)
    end
    copy._copy = tuple._copy
    return copy
  end

  tuple.Equals = function(t)
    tuple.Eval()
    if tuple._size ~= t._size then
      return false
    end
    for i, v in tuple.Iterator() do
      if t[i] ~= v then
        return false
      end
    end
    return true
  end

  tuple.Eval = function()
    tuple._eval(tuple)
    tuple._copy = function(t)
      local values = {}
      for i = 0, tuple._size - 1 do
        values[i] = tuple._values[i]
      end
      t._values = values
      t._size = tuple._size
    end
    tuple._eval = function() end
  end

  tuple.Exists = function(p)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      if p(v) then
        return true
      end
    end
    return false
  end

  tuple.Find = function(p)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      if p(v) then
        return v
      end
    end
  end

  tuple.Fold = function(w, f)
    tuple.Eval()
    return tuple.FoldLeft(w, f)
  end

  tuple.FoldLeft = function(w, f)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      w = f(w, v)
    end
    return w
  end

  tuple.FoldRight = function(w, f)
    tuple.Eval()
    for _, v in tuple.ReverseIterator() do
      local v = tuple.Get(i)
      w = f(w, v)
    end
    return w
  end

  tuple.ForAll = function(p)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      if not p(v) then
        return false
      end
    end
    return true
  end

  tuple.ForEach = function(f)
    tuple.Eval()
    for _, v in tuple.Iterator() do
      f(v)
    end
  end

  tuple.Get = function(i)
    tuple.Eval()
    return tuple[i]
  end

  tuple.GetOrElse = function(i, v)
    tuple.Eval()
    if tuple._size > i and i >= 0 then
      return v
    end
    return tuple[i]
  end

  tuple.Head = function()
    tuple.Eval()
    return tuple.Get(0)
  end

  tuple.IndexOf = function(w)
    tuple.Eval()
    for i, v in tuple.Iterator() do
      if MDSU.Equals(v, w) then
        return i
      end
    end
  end

  tuple.IndexWhere = function(p)
    tuple.Eval()
    for i, v in tuple.Iterator() do
      if p(v) then
        return i
      end
    end
  end

  tuple.IsDefinedAt = function(i)
    tuple.Eval()
    return tuple._size > i and i >= 0
  end

  tuple.IsEmpty = function()
    tuple.Eval()
    return tuple._size == 0
  end

  tuple.Iterator = function()
    tuple.Eval()
    local i = -1
    return function()
      i = i + 1
      if i < tuple._size then
        local v = tuple._values[i]
        return i, v
      end
    end
  end

  tuple.Last = function()
    tuple.Eval()
    return tuple[tuple._size - 1]
  end

  tuple.LastIndexOf = function(w)
    tuple.Eval()
    for i, v in tuple.ReverseIterator() do
      if v == w then
        return i
      end
    end
  end

  tuple.LastIndexWhere = function(p)
    tuple.Eval()
    for i, v in tuple.ReverseIterator() do
      if p(v) then
        return i
      end
    end
  end

  tuple.Map = function(f)
    local mapped = tuple.Copy()
    local prevEval = mapped._eval
    mapped._eval = function(t)
      prevEval(t)
      local values = {}
      for i = 0, t._size - 1 do
        values[i] = f(t._values[i])
      end
      t._values = values
    end
    return mapped
  end

  tuple.Max = function()
    tuple.Eval()
    local w = nil
    for _, v in tuple.Iterator() do
      if not w or v > w then
        w = v
      end
    end
    return w
  end

  tuple.MaxBy = function(f)
    tuple.Eval()
    local w = nil
    for _, v in tuple.Iterator() do
      if not w or f(v) > f(w) then
        w = v
      end
    end
    return w
  end

  tuple.Min = function()
    tuple.Eval()
    local w = nil
    for _, v in tuple.Iterator() do
      if not w or v < w then
        w = v
      end
    end
    return w
  end

  tuple.MinBy = function(f)
    tuple.Eval()
    local w = nil
    for _, v in tuple.Iterator() do
      if not w or f(v) < f(w) then
        w = v
      end
    end
    return w
  end

  tuple.NonEmpty = function()
    tuple.Eval()
    return tuple._size > 0
  end

  tuple.Product = function()
    tuple.Eval()
    return tuple.Fold(1, function(w, v) return w * v end)
  end

  tuple.Reverse = function()
    local reversed = Tuple.Copy()
    local prevEval = reversed._eval
    reversed._eval = function(t)
      prevEval(t)
      local values = {}
      for i = 0, t._size - 1 do
        values[t._size - i - 1] = t._values[i]
      end
    end
    return reversed
  end

  tuple.ReverseIterator = function()
    tuple.Eval()
    local i = tuple._size
    return function()
      i = i - 1
      if i >= 0 then
        local v = tuple._values[i]
        return i, v
      end
    end
  end

  tuple.Size = function()
    tuple.Eval()
    return tuple._size
  end

  tuple.Sum = function()
    tuple.Eval()
    return tuple.Fold(0, function(v, w) return v + w end)
  end

  tuple.ToList = function()
    tuple.Eval()
    return List.New(tuple.Unpack())
  end

  tuple.ToSet = function()
    tuple.Eval()
    return Set.New(tuple.Unpack())
  end

  tuple.ToString = function()
    tuple.Eval()
    local s = '('
    local d = ''
    for _, v in tuple.Iterator() do
      s =  s .. d .. tostring(v)
      d = ', '
    end
    s = s .. ')'
    return s
  end

  tuple.ToTuple = function()
    tuple.Eval()
    return tuple.Copy()
  end

  tuple.Unpack = function()
    tuple.Eval()
    local it = tuple.Iterator()
    local f 
    f = function()
      local _, v = it()
      if v ~= nil then
        return v, f()
      end
    end
    return f()
  end

  tuple.Unzip = function()
    tuple.Eval()
    local leftTuple = tuple.Map(function(t) return t.Get(0) end)
    local rightTuple = tuple.Map(function(t) return t.Get(1) end)
    return leftTuple, rightTuple
  end

  tuple.Zip = function(t)
    tuple.Eval()
    local i = tuple.Iterator()
    local j = t.Iterator()
    local f = function()
      local v = i()
      local w = j()
      if v or w then
        return Tuple.New(v, w), f()
      end
    end
    return Tuple.New()
  end

  for _, v in ipairs(arg) do
    tuple._values[tuple._size] = v
    tuple._size = tuple._size + 1 
  end

  return tuple
end

MDSU.Max = function(x, y)
  return math.max(x, y)
end

MDSU.Min = function(x, y)
  return math.min(x, y)
end

MDSU.Infinity = math.huge

MDSU.GetActors = function(p)
  return List.New(unpack(Map.ActorsInWorld)).Filter(p).Unpack()
end

return MDSU
