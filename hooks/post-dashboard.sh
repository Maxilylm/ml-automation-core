#!/bin/bash
# Post-Dashboard hook: Validates and prepares Streamlit dashboard
# Usage: Called after dashboard creation in team-coldstart workflow
# Validates syntax (ast.parse), placeholders, and import-level errors.

set -e

DASHBOARD_PATH="${1:-dashboard/app.py}"

echo "[Post-Dashboard Hook] Validating dashboard..."

# 1. Check dashboard file exists
if [ ! -f "$DASHBOARD_PATH" ]; then
    echo "  - ERROR: Dashboard not found at $DASHBOARD_PATH"
    exit 1
fi

echo "  - Dashboard file found"

# 2. Validate syntax via ast.parse (stricter than py_compile)
echo "  - Checking syntax with ast.parse..."
python3 -c "
import ast, sys
with open('$DASHBOARD_PATH', 'r') as f:
    source = f.read()
try:
    ast.parse(source)
except SyntaxError as e:
    print(f'  - ERROR: SyntaxError: {e}')
    sys.exit(1)
print('    Syntax OK')
" || exit 1

# 3. Validate all plotly color values (catches invalid names, bad hex, None, NaN, etc.)
echo "  - Validating plotly color values..."
python3 -c "
import re, sys, ast

with open('$DASHBOARD_PATH', 'r') as f:
    source = f.read()

# CSS named colors supported by plotly (W3C CSS3 specification, 147 colors)
VALID_CSS_COLORS = {
    'aliceblue','antiquewhite','aqua','aquamarine','azure','beige','bisque','black',
    'blanchedalmond','blue','blueviolet','brown','burlywood','cadetblue','chartreuse',
    'chocolate','coral','cornflowerblue','cornsilk','crimson','cyan','darkblue',
    'darkcyan','darkgoldenrod','darkgray','darkgreen','darkgrey','darkkhaki',
    'darkmagenta','darkolivegreen','darkorange','darkorchid','darkred','darksalmon',
    'darkseagreen','darkslateblue','darkslategray','darkslategrey','darkturquoise',
    'darkviolet','deeppink','deepskyblue','dimgray','dimgrey','dodgerblue','firebrick',
    'floralwhite','forestgreen','fuchsia','gainsboro','ghostwhite','gold','goldenrod',
    'gray','green','greenyellow','grey','honeydew','hotpink','indianred','indigo',
    'ivory','khaki','lavender','lavenderblush','lawngreen','lemonchiffon','lightblue',
    'lightcoral','lightcyan','lightgoldenrodyellow','lightgray','lightgreen','lightgrey',
    'lightpink','lightsalmon','lightseagreen','lightskyblue','lightslategray',
    'lightslategrey','lightsteelblue','lightyellow','lime','limegreen','linen','magenta',
    'maroon','mediumaquamarine','mediumblue','mediumorchid','mediumpurple',
    'mediumseagreen','mediumslateblue','mediumspringgreen','mediumturquoise',
    'mediumvioletred','midnightblue','mintcream','mistyrose','moccasin','navajowhite',
    'navy','oldlace','olive','olivedrab','orange','orangered','orchid',
    'palegoldenrod','palegreen','paleturquoise','palevioletred','papayawhip',
    'peachpuff','peru','pink','plum','powderblue','purple','rebeccapurple','red',
    'rosybrown','royalblue','saddlebrown','salmon','sandybrown','seagreen','seashell',
    'sienna','silver','skyblue','slateblue','slategray','slategrey','snow',
    'springgreen','steelblue','tan','teal','thistle','tomato','turquoise','violet',
    'wheat','white','whitesmoke','yellow','yellowgreen'
}

def is_valid_color(s):
    \"\"\"Check if a string is a valid plotly color value.\"\"\"
    s = s.strip().lower()
    if s in VALID_CSS_COLORS:
        return True
    # hex: #RGB, #RRGGBB, #RRGGBBAA
    if re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$', s):
        return True
    # rgb(r,g,b) or rgba(r,g,b,a)
    if re.match(r'^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+\s*)?\)$', s):
        return True
    # hsla, hsva variants
    if re.match(r'^hsla?\(\s*\d+\s*,\s*[\d.]+%?\s*,\s*[\d.]+%?\s*(,\s*[\d.]+\s*)?\)$', s):
        return True
    return False

# Find all color=<string_literal> assignments in source
issues = []
# Pattern: color= followed by a quoted string (single or double)
for m in re.finditer(r'color\s*=\s*([\"\\'])(.*?)\1', source):
    color_val = m.group(2)
    if not is_valid_color(color_val):
        lineno = source[:m.start()].count('\n') + 1
        issues.append(f'Line {lineno}: color=\"{color_val}\" is not a valid plotly color')

# Also catch color=None, color=NaN, color=\"\"
for m in re.finditer(r'color\s*=\s*(None|float\([\"\\']nan[\"\\']\))', source):
    lineno = source[:m.start()].count('\n') + 1
    issues.append(f'Line {lineno}: color={m.group(1)} is invalid')

if issues:
    print('  - ERROR: Invalid plotly color values found:')
    for issue in issues:
        print(f'    {issue}')
    print()
    print('    Valid formats: CSS named colors (e.g. \"lightcoral\", \"steelblue\"),')
    print('    hex (\"#FF0000\"), rgb (\"rgb(255,0,0)\"), rgba (\"rgba(255,0,0,0.5)\")')
    print('    Full list: https://plotly.com/python/css-colors/')
    sys.exit(1)
print('    All color values valid')
" || exit 1

# 4. Check for unresolved placeholder strings like "{value}", "{count}", "{Project}"
echo "  - Checking for unresolved placeholders..."
python3 -c "
import re, sys
with open('$DASHBOARD_PATH', 'r') as f:
    source = f.read()
# Match quoted strings that are just a placeholder: \"{something}\"
placeholders = re.findall(r'\"\\{[A-Za-z_][A-Za-z0-9_]*\\}\"', source)
if placeholders:
    print(f'  - ERROR: Unresolved placeholders found: {placeholders}')
    print('    Dashboard must use actual computed values, not template strings.')
    sys.exit(1)
print('    No placeholders found')
" || exit 1

# 5. Import-level check (catches NameError/ImportError, tolerates Streamlit runtime errors)
echo "  - Running import-level validation..."
python3 -c "
import sys, types, importlib, importlib.util

# Mock streamlit so we don't need a running server
mock_st = types.ModuleType('streamlit')
# Add common streamlit attributes as no-ops so basic attribute access doesn't fail
class _MockCallable:
    def __call__(self, *a, **kw): return self
    def __getattr__(self, name): return _MockCallable()
for attr in ['set_page_config', 'title', 'header', 'subheader', 'write', 'markdown',
             'sidebar', 'columns', 'tabs', 'metric', 'dataframe', 'plotly_chart',
             'pyplot', 'altair_chart', 'selectbox', 'multiselect', 'slider',
             'text_input', 'number_input', 'button', 'checkbox', 'radio',
             'expander', 'container', 'empty', 'spinner', 'success', 'error',
             'warning', 'info', 'cache_data', 'cache_resource', 'session_state',
             'file_uploader', 'download_button', 'form', 'form_submit_button',
             'divider', 'caption', 'code', 'latex', 'table', 'json', 'image',
             'audio', 'video', 'balloons', 'snow', 'toast', 'status',
             'toggle', 'color_picker', 'date_input', 'time_input', 'text_area',
             'progress', 'echo', 'help', 'experimental_rerun', 'rerun', 'stop',
             'navigation', 'page_link', 'logo', 'html', 'Page', 'dialog',
             'fragment', 'popover', 'pills', 'segmented_control', 'feedback',
             'context', 'secrets', 'query_params', 'chat_input', 'chat_message']:
    setattr(mock_st, attr, _MockCallable())
sys.modules['streamlit'] = mock_st
sys.modules['streamlit.components'] = types.ModuleType('streamlit.components')
sys.modules['streamlit.components.v1'] = types.ModuleType('streamlit.components.v1')

try:
    spec = importlib.util.spec_from_file_location('dashboard_check', '$DASHBOARD_PATH')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
except NameError as e:
    print(f'  - ERROR: Undefined variable: {e}')
    sys.exit(1)
except ImportError as e:
    print(f'  - ERROR: Import error: {e}')
    sys.exit(1)
except Exception:
    # Tolerate other errors (missing data files, runtime Streamlit calls, etc.)
    pass
finally:
    sys.modules.pop('streamlit', None)
    sys.modules.pop('streamlit.components', None)
    sys.modules.pop('streamlit.components.v1', None)

print('    Import-level check OK')
" || exit 1

# 6. Check for required Streamlit imports
echo "  - Checking Streamlit imports..."
if ! grep -q "import streamlit" "$DASHBOARD_PATH"; then
    echo "  - WARNING: Missing 'import streamlit' statement"
fi

# 7. Check for page config (best practice)
if ! grep -q "st.set_page_config" "$DASHBOARD_PATH"; then
    echo "  - TIP: Consider adding st.set_page_config() for better UX"
fi

# 8. Check for required components
echo "  - Checking dashboard components..."
COMPONENTS=("st.title\|st.header" "st.metric\|st.dataframe" "st.plotly_chart\|st.pyplot\|st.altair_chart")
for comp in "${COMPONENTS[@]}"; do
    if grep -qE "$comp" "$DASHBOARD_PATH"; then
        echo "    Found: $(echo $comp | sed 's/\\|/ or /g')"
    fi
done

# 9. Create requirements snippet for dashboard
if [ ! -f "dashboard/requirements.txt" ]; then
    echo "  - Generating dashboard requirements..."
    mkdir -p dashboard
    cat > dashboard/requirements.txt << 'EOF'
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.18.0
numpy>=1.24.0
EOF
    echo "    Created dashboard/requirements.txt"
fi

# 10. Create run script
if [ ! -f "dashboard/run.sh" ]; then
    echo "  - Creating run script..."
    cat > dashboard/run.sh << 'EOF'
#!/bin/bash
# Run the Streamlit dashboard locally
streamlit run app.py --server.port 8501 --server.address localhost
EOF
    chmod +x dashboard/run.sh
    echo "    Created dashboard/run.sh"
fi

# 11. Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Dashboard validated: $DASHBOARD_PATH" >> .claude/workflow.log 2>/dev/null || true

echo "[Post-Dashboard Hook] Dashboard ready!"
echo ""
echo "  To run locally: cd dashboard && streamlit run app.py"
echo "  Or use: ./dashboard/run.sh"
