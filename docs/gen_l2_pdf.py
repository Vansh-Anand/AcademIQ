from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

BLUE = colors.HexColor('#0EA5E9')
GREEN = colors.HexColor('#00C896')
ORANGE = colors.HexColor('#F59E0B')
MED_TEXT = colors.HexColor('#C9D1D9')
DIM_TEXT = colors.HexColor('#8B949E')
ACCENT_BG = colors.HexColor('#161B22')
DARK_BORDER = colors.HexColor('#30363D')

doc = SimpleDocTemplate(
    'docs/l2-sdn.pdf',
    pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle('Title', parent=styles['Title'],
    fontSize=22, fontName='Helvetica-Bold', textColor=BLUE,
    spaceAfter=4, alignment=TA_LEFT)

h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
    fontSize=14, fontName='Helvetica-Bold', textColor=GREEN,
    spaceBefore=14, spaceAfter=6)

body_style = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica', textColor=MED_TEXT,
    spaceAfter=6, leading=16, alignment=TA_JUSTIFY)

bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica', textColor=MED_TEXT,
    spaceAfter=4, leading=15, leftIndent=20)

sub_bullet_style = ParagraphStyle('SubBullet', parent=styles['Normal'],
    fontSize=9.5, fontName='Helvetica', textColor=MED_TEXT,
    spaceAfter=3, leading=14, leftIndent=40)

meta_style = ParagraphStyle('Meta', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica', textColor=DIM_TEXT,
    spaceAfter=2)


def c(txt):
    """Wrap in Courier green."""
    return f'<font name="Courier" color="#00C896">{txt}</font>'


content = []

# Header
content.append(Paragraph('Layer 2: Semantic Defense Network (SDN)', title_style))
content.append(Paragraph('AcademIQ Security Architecture — L2 Component Documentation', meta_style))
content.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=12))

# Intro
content.append(Paragraph(
    'The Semantic Defense Network intercepts commands that have structurally bypassed L1 GCD '
    'and evaluates them for semantic safety before passing them to the execution layer. It relies '
    'on a rigorous 5-pass normalization algorithm to resolve obfuscation statically.',
    body_style))

# Architecture
content.append(Paragraph('Architecture', h2_style))

arch = [
    (
        'Interceptor',
        'Entry point (' + c('ShellInterceptor') + '). Uses '
        + c('LinuxLDPreloadInterceptor') + ' or ' + c('LinuxEBPFUprobeInterceptor')
        + ' structurally in production; simulated in development via '
        + c('DevelopmentShellInterceptor') + '.'
    ),
    (
        'Parser',
        'Uses Python\'s ' + c('bashlex') + ' library to tokenize POSIX shell commands safely '
        'into an AST without executing any sub-process.'
    ),
    (
        'Five-Pass Normalizer',
        'Resolves all known obfuscation layers in strict sequential order (see sub-steps below).'
    ),
    (
        'Policy Matcher',
        'Evaluates the resulting ' + c('CanonicalCommand') + ' against rules defined in '
        + c('config/policies/shell.yaml') + ' using a fast allow/deny evaluator.'
    ),
    (
        'TOCTOU Resolver',
        'Records the ' + c('inode') + ' and ' + c('device_id') + ' of target paths using '
        + c('os.stat()') + ' at decision time to prevent time-of-check-to-time-of-use races.'
    ),
    (
        'Execution Gate',
        'Strictly enforces: ' + c('L1 ALLOW + L2 BLOCK = NO EXECUTION') + '.'
    ),
]

for i, (name, desc) in enumerate(arch, 1):
    content.append(Paragraph(f'{i}. <b>{name}</b> \u2014 {desc}', bullet_style))

# Five passes
passes = [
    (
        'Pass 1 \u2014 Variable Expansion',
        'Safe, static resolution of environment variables against a predefined '
        + c('SafeEnvironmentSnapshot') + '. Unresolvable variables fail closed.'
    ),
    (
        'Pass 2 \u2014 Encoding Decode',
        'Detects and decodes HEX (' + c('\\\\x72\\\\x6d') + '), OCTAL (' + c('\\\\162\\\\155')
        + '), BASE64 (' + c('cm0=') + '), and URL encoding safely \u2014 no shell execution.'
    ),
    (
        'Pass 3 \u2014 ANSI-C Quoting',
        'Normalizes strings like ' + c("$'r\\\\x6d'") + ' into ' + c('rm')
        + '. Handles escape sequences recursively.'
    ),
    (
        'Pass 4 \u2014 Alias/Function Resolution',
        'Applies known aliases from a safe shell metadata snapshot (e.g., '
        + c('ll') + ' \u2192 ' + c('ls -la') + ').'
    ),
    (
        'Pass 5 \u2014 Canonicalization',
        'Strict path canonicalization: resolves ' + c('/./') + ' and ' + c('/../')
        + ' traversal, removes shell quoting artifacts, normalizes whitespace.'
    ),
]

for name, desc in passes:
    content.append(Paragraph(f'<b>{name}:</b> {desc}', sub_bullet_style))

content.append(Spacer(1, 0.4 * cm))

# Static validation model
content.append(Paragraph('Static Validation Model', h2_style))
content.append(Paragraph(
    'Crucially, <b>no command execution occurs during normalization</b>. Command substitutions '
    'such as subshell invocations are marked as unresolved. In strict mode, unresolved substitutions '
    'trigger a hard <b>BLOCK</b> to fail closed, preventing any ambiguous command from reaching '
    'the execution layer.',
    body_style))

# Platform limitations
content.append(Paragraph('Platform Limitations (Windows)', h2_style))

plat = [
    (
        'TOCTOU',
        'Linux can use ' + c('O_PATH') + ' for robust lockless resolution. On Windows, we rely '
        'on checking ' + c('st_ino') + ' (FileIndex) and ' + c('st_dev')
        + ' immediately before execution.'
    ),
    (
        'Paths',
        'The canonicalizer ensures cross-platform consistency by mapping ' + c('\\\\')
        + ' to ' + c('/') + ' internally after ' + c('realpath') + ' resolution. '
        'Native LD_PRELOAD interceptors are structurally mocked on Windows.'
    ),
    (
        'eBPF Uprobe',
        c('LinuxEBPFUprobeInterceptor') + ' raises ' + c('NotImplementedError')
        + ' on non-Linux platforms. Use ' + c('DevelopmentShellInterceptor')
        + ' for local development and testing.'
    ),
]

for name, desc in plat:
    content.append(Paragraph(f'\u2022 <b>{name}</b> \u2014 {desc}', bullet_style))

content.append(Spacer(1, 0.4 * cm))

# Event schema
content.append(Paragraph('Event Schema', h2_style))
content.append(Paragraph(
    'L2 emits ' + c('NormalizedCommandEvent') + ' after processing every intercepted shell command. '
    'This event is consumed by the orchestrator and persisted to the L6 ECES evidence chain.',
    body_style))

schema_fields = [
    ('event_id', 'Unique identifier for this normalized event'),
    ('agent_id', 'Agent session identifier (propagated from original ToolInvocationEvent)'),
    ('command_text', 'Canonical command string after all 5 normalization passes'),
    ('original_command_hash', 'SHA-256 of the raw, unmodified command string'),
    ('canonical_command_hash', 'SHA-256 of the fully normalized canonical command'),
    ('normalization_passes', 'Ordered list of transformation passes applied'),
    ('obfuscation_detected', 'Boolean: True if any encoding/obfuscation was found and normalized'),
    ('policy_result', 'Final decision: ALLOW | BLOCK | REVIEW'),
    ('matched_rule', 'Identifier of the policy rule that determined the decision'),
    ('path_identities', 'TOCTOU resolution locks: inode + device_id per resolved path'),
    ('security_decision', 'Final security decision propagated to the orchestrator'),
]

for field, desc in schema_fields:
    content.append(Paragraph(
        c(field) + '  \u2014  ' + desc,
        sub_bullet_style))

content.append(Spacer(1, 0.5 * cm))
content.append(HRFlowable(width='100%', thickness=1, color=DARK_BORDER))
content.append(Spacer(1, 0.2 * cm))
content.append(Paragraph(
    'Source: l2_sdn/ \u00b7 Policy: config/policies/shell.yaml \u00b7 '
    'Tests: tests/integration/test_l2_adversarial.py (20 passing)',
    meta_style))

doc.build(content)
print('PDF generated successfully: docs/l2-sdn.pdf')
