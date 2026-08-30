from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
import os

BLUE = colors.HexColor('#0EA5E9')
GREEN = colors.HexColor('#00C896')
ORANGE = colors.HexColor('#F59E0B')
MED_TEXT = colors.HexColor('#C9D1D9')
DIM_TEXT = colors.HexColor('#8B949E')
ACCENT_BG = colors.HexColor('#161B22')
DARK_BORDER = colors.HexColor('#30363D')

doc = SimpleDocTemplate(
    'docs/experiments-current-state.pdf',
    pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle('Title', parent=styles['Title'],
    fontSize=22, fontName='Helvetica-Bold', textColor=BLUE,
    spaceAfter=4, alignment=TA_LEFT)

h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
    fontSize=13, fontName='Helvetica-Bold', textColor=GREEN,
    spaceBefore=12, spaceAfter=4)

body_style = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica', textColor=MED_TEXT,
    spaceAfter=6, leading=16, alignment=TA_JUSTIFY)

bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica', textColor=MED_TEXT,
    spaceAfter=4, leading=15, leftIndent=20)

meta_style = ParagraphStyle('Meta', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica', textColor=DIM_TEXT,
    spaceAfter=2)

def c(txt):
    """Wrap in Courier green."""
    return f'<font name="Courier" color="#00C896">{txt}</font>'

content = []

# Header
content.append(Paragraph('Existing Experiment Infrastructure', title_style))
content.append(Paragraph('AcademIQ Project Assessment', meta_style))
content.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=12))


items = [
    (
        '1. Existing benchmark components',
        'The ' + c('benchmarks/') + ' directory currently houses isolated performance benchmarks:<br/>'
        '\u2022 <b>L1 GCD</b>: ' + c('benchmarks/gcd_real_model/benchmark_gcd.py') + ' (Tokens/sec and generation overhead).<br/>'
        '\u2022 <b>L2 SDN</b>: ' + c('benchmarks/latency/sdn_benchmark.py') + ' (Normalization latency).<br/>'
        '\u2022 <b>L3 Native</b>: ' + c('benchmarks/linux_native/l3_validation_runner.py') + ' (Linux kernel hook validation).'
    ),
    (
        '2. Existing test fixtures',
        '\u2022 ' + c('tests/fixtures/telemetry/execve_trace.jsonl') + ' contains pre-recorded benign and malicious system call traces for testing L3/L4 offline.<br/>'
        '\u2022 ' + c('tests/integration/') + ' contains dozens of hardcoded adversarial logic test cases (e.g., 20 distinct obfuscation payloads for L2, multi-step exfiltration flows for L5).'
    ),
    (
        '3. Event injection capabilities',
        '\u2022 <b>Agent/L1 Action</b>: Fully injectable via ' + c('AcademiqOrchestrator.process_event(ToolInvocationEvent(...))') + '<br/>'
        '\u2022 <b>L2 Shell</b>: Fully injectable directly via ' + c('L2Interceptor.intercept(ShellCommandEvent(...))') + '<br/>'
        '\u2022 <b>L3 Telemetry</b>: Fully injectable via ' + c('SimulatedL3Collector.run_replay()') + ' loading arbitrary JSON traces.'
    ),
    (
        '4. L1 integration capability',
        '\u2022 The repository already contains a real-model HuggingFace wrapper (' + c('GCDLogitsProcessor')
        + ') that successfully restricts token generation via the PDA compiled from ' + c('config/policies/gcd.yaml') + '.'
    ),
    (
        '5. L2 integration capability',
        '\u2022 The ' + c('DevelopmentShellInterceptor') + ' natively canonicalizes complex shell commands, stripping '
        'base64/ANSI-C/path traversal obfuscation before checking against allowed policies.'
    ),
    (
        '6. L3 simulation capability',
        '\u2022 ' + c('SimulatedL3Collector') + ' allows completely native-free Windows execution by processing '
        + c('.jsonl') + ' trace files and triggering the standard L3/L4 callbacks.'
    ),
    (
        '7. L4 invocation capability',
        '\u2022 The ' + c('IsolationForestDetector') + ' can ingest numerical feature arrays (representing syscall paths) '
        'directly and output divergence scores without requiring real live kernel telemetry.'
    ),
    (
        '8. L5 invocation capability',
        '\u2022 ' + c('BayesianRiskModel') + ' dynamically calculates multi-step attack probabilities.<br/>'
        '\u2022 ' + c('FuzzyGovernanceEngine') + ' dictates ALLOW, WARN, THROTTLE, or FREEZE states programmatically '
        'based on the rolling Bayesian evidence.'
    ),
    (
        '9. ECES evidence capability',
        '\u2022 ' + c('EvidenceChainWriter') + ' automatically logs security events into an append-only store with '
        'cryptographic hash chaining (BLAKE3/SHA256).'
    ),
    (
        '10. Existing metrics',
        '\u2022 Output from test suites and benchmarks already measures sub-millisecond execution times in L1/L2, '
        'and isolation accuracy in L4. The pipeline naturally timestamps events (using ' + c('time.time_ns()')
        + '), making latency tracking trivial.'
    ),
    (
        '11. Existing CLI support',
        '\u2022 The CLI (' + c('cli/main.py') + ') supports simulated pipeline runs (' + c('run --mode simulation')
        + '), manual SDN normalization analysis (' + c('sdn analyze') + '), and hardware status checks.'
    ),
    (
        '12. Reusable components',
        '\u2022 The ' + c('AcademiqOrchestrator') + ' itself acts as a unified entrypoint.<br/>'
        '\u2022 The scenarios in ' + c('test_l5_riskchain.py') + ' act as a miniature sequencing framework that can '
        'be lifted and expanded for the 5 formal experiments.'
    ),
    (
        '13. Missing components',
        '\u2022 <b>Unified Scenario Harness</b>: Currently, L1/L2 testing and L3/L4 telemetry replay are completely '
        'isolated in their respective unit/integration test files. We lack a unified ' + c('ExperimentRunner')
        + ' that simultaneously feeds a malicious ' + c('ToolInvocationEvent') + ' <i>and</i> an accompanying '
        'L3 Trace to represent a single, cohesive attacker payload moving through all defenses.'
    ),
    (
        '14. Minimum changes required for EXP-1',
        '\u2022 Create a reusable experiment runner script.<br/>'
        '\u2022 Define EXP-1 (Direct Prompt Injection) as an object combining a forbidden ' + c('ToolInvocationEvent')
        + ' (e.g. ' + c('sys_exec') + ') with a mocked L3 telemetry file (should it hypothetically bypass L1/L2).<br/>'
        '\u2022 Route it through the existing orchestrator and verify that the pipeline correctly terminates the attack '
        'at L1/L2 (emitting ' + c('DecisionEnum.BLOCK') + ').'
    ),
    (
        '15. Recommended next implementation step',
        'Create ' + c('benchmarks/experiments/runner.py') + ' and implement a base ' + c('ExperimentHarness')
        + ' class capable of taking a ' + c('ScenarioDefinition') + ' (consisting of Agent Events and simulated L3 Traces) '
        'and executing it end-to-end through the existing ' + c('AcademiqOrchestrator') + '.'
    ),
]

for title, text in items:
    content.append(Paragraph(title, h2_style))
    content.append(Paragraph(text, body_style))


content.append(Spacer(1, 0.5 * cm))
content.append(HRFlowable(width='100%', thickness=1, color=DARK_BORDER))
content.append(Spacer(1, 0.2 * cm))
content.append(Paragraph(
    'Status: Assessment Completed',
    meta_style))

doc.build(content)
print('PDF generated successfully: docs/experiments-current-state.pdf')
