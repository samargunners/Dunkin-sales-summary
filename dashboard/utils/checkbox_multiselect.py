import streamlit as st

def checkbox_multiselect(label: str, options: list, key: str, default=None, in_sidebar=False):
    """
    Checkbox-based multi-select with search, 'Select All', 'Clear', and 'Filter' buttons.
    Returns: list of selected options.
    """
    if default is None:
        default = options

    sel_key = f"{key}_selected"
    search_key = f"{key}_search"
    tick_keys_key = f"{key}_tick_keys"

    if sel_key not in st.session_state:
        st.session_state[sel_key] = list(default)
    if search_key not in st.session_state:
        st.session_state[search_key] = ""
    if tick_keys_key not in st.session_state:
        st.session_state[tick_keys_key] = {opt: f"{key}_opt_{i}" for i, opt in enumerate(options)}

    container = st.sidebar if in_sidebar else st
    use_popover = hasattr(st, "popover")
    wrapper = container.popover(label) if use_popover else container.expander(label, expanded=False)

    with wrapper:
        # Search box
        st.session_state[search_key] = st.text_input("Search", value=st.session_state[search_key], key=f"{key}_searchbox")
        q = st.session_state[search_key].strip().lower()
        filtered = [o for o in options if q in str(o).lower()] if q else options

        current_sel = set(st.session_state[sel_key])
        all_filtered_selected = len(filtered) > 0 and all(o in current_sel for o in filtered)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.checkbox("Select All", value=all_filtered_selected, key=f"{key}_select_all"):
                current_sel = current_sel.union(set(filtered))
        with col2:
            if st.button("Clear", key=f"{key}_clear_btn"):
                current_sel = current_sel.difference(set(filtered))

        if len(filtered) == 0:
            st.caption("No results.")
        else:
            for o in filtered:
                ck = st.session_state[tick_keys_key][o]
                checked = o in current_sel
                new_checked = st.checkbox(str(o), value=checked, key=ck)
                if new_checked:
                    current_sel.add(o)
                else:
                    current_sel.discard(o)

        _ = st.button("Filter", type="primary", key=f"{key}_apply_btn")  # cosmetic; state already applied
        st.session_state[sel_key] = sorted(current_sel)

    return st.session_state[sel_key]
