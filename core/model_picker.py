def pick_first_available(preferred, available, global_fallback):
    if not available:
        return preferred[0] if preferred else global_fallback[0]
    for m in preferred:
        if m in available:
            return m
    for m in global_fallback:
        if m in available:
            return m
    return global_fallback[-1]
