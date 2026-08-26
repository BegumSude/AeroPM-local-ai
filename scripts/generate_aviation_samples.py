"""One-off generator for the synthetic AeroPM demo documents.

Not part of the runtime RAG pipeline. Produces real, text-layer PDFs under
data/samples/aviation/ so document_loader can extract text from them
(unlike a scanned/image-only PDF). Run with: python3 scripts/generate_aviation_samples.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "samples" / "aviation"

STYLES = getSampleStyleSheet()


def _render(filename: str, title: str, paragraphs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT_DIR / filename), pagesize=LETTER)
    story = [Paragraph(title, STYLES["Title"]), Spacer(1, 12)]
    for paragraph in paragraphs:
        story.append(Paragraph(paragraph, STYLES["BodyText"]))
        story.append(Spacer(1, 10))
    doc.build(story)


def generate_project_charter() -> None:
    _render(
        "project_charter.pdf",
        "Project Charter: Aircraft Avionics Upgrade Project",
        [
            "Sponsoring organization: Nordholm Avionics Systems.",
            "Project sponsor: David Whitfield, VP Engineering.",
            "Project manager: Sofia Reyes.",
            "Project start date: January 10, 2027. Target delivery date: July 30, 2027.",
            "Project objective: upgrade the flight management, GPS positioning, and autopilot "
            "integration systems across the regional aircraft fleet to meet updated FAA avionics "
            "standards and improve navigation accuracy.",
            "Scope includes: GPS receiver replacement, flight management software upgrade, "
            "autopilot interface integration, cabin display unit upgrade, and full FAA "
            "certification of the upgraded systems.",
            "Out of scope: engine control systems, cabin entertainment systems, and airframe "
            "structural modifications.",
            "Key stakeholders: Procurement (Elena Kovacs), Software Integration (Marcus Chen), "
            "Quality Assurance (Amara Osei).",
        ],
    )


def generate_requirements() -> None:
    _render(
        "requirements.pdf",
        "Requirements Specification: Aircraft Avionics Upgrade Project",
        [
            "REQ-001: The avionics system shall report GPS position accuracy within 2 meters CEP "
            "(Circular Error Probable). Status: In progress.",
            "REQ-002: The flight management system shall interface with the legacy autopilot "
            "module via an ARINC 429 data bus. Status: In progress.",
            "REQ-003: The system shall log all avionics events with timestamp accuracy of 10 "
            "milliseconds or better. Status: Completed.",
            "REQ-004: The cabin display unit shall support a night-vision-compatible lighting "
            "mode. Status: Not started.",
            "REQ-005: The system shall complete its cold boot sequence in under 45 seconds. "
            "Status: In progress.",
        ],
    )


def generate_project_plan() -> None:
    _render(
        "project_plan.pdf",
        "Project Plan: Aircraft Avionics Upgrade Project",
        [
            "MS-001 Kickoff: due January 10, 2027. Status: Completed.",
            "MS-002 Software Integration: due February 20, 2027. Status: On track.",
            "MS-003 Integration Testing: due March 15, 2027. Status: Delayed, due to a GPS "
            "antenna supplier manufacturing delay (see RISK-001).",
            "MS-004 FAA Compliance Review: due May 1, 2027. Status: On track.",
            "MS-005 Final Delivery: due July 30, 2027. Status: On track.",
        ],
    )


def generate_risk_register() -> None:
    _render(
        "risk_register.pdf",
        "Risk Register: Aircraft Avionics Upgrade Project",
        [
            "RISK-001: The GPS antenna supplier has reported a 6-week manufacturing delay due to "
            "a component shortage. Probability: High. Impact: High. This directly threatens the "
            "Integration Testing milestone scheduled for March 2027. Responsible: Procurement "
            "Team (Elena Kovacs).",
            "RISK-002: The avionics software team has identified a potential incompatibility "
            "between the new flight control firmware and the legacy autopilot module. "
            "Probability: Medium. Impact: High. This threatens the Software Integration "
            "milestone. Responsible: Software Integration Lead (Marcus Chen).",
            "RISK-003: Cabin wiring harness certification documentation from the subcontractor "
            "is incomplete, which could delay the FAA Compliance Review. Probability: Low. "
            "Impact: Medium. Responsible: Quality Assurance (Amara Osei).",
            "RISK-004: The night-vision-compatible display supplier has not confirmed a sample "
            "delivery date, threatening REQ-004. Probability: Medium. Impact: Medium. "
            "Responsible: Project Manager (Sofia Reyes).",
        ],
    )


def generate_meeting_minutes_01() -> None:
    _render(
        "meeting_minutes_01.pdf",
        "Meeting Minutes: Project Status Review, January 15, 2027",
        [
            "Attendees: Sofia Reyes, Elena Kovacs, Marcus Chen, Amara Osei.",
            "Decision: the team agreed to add a 3-week schedule buffer before Integration "
            "Testing to absorb the GPS antenna supplier delay. Reason: mitigate RISK-001. "
            "Affected area: Integration Testing milestone.",
            "Decision: the firmware incompatibility identified in RISK-002 will be escalated to "
            "Marcus Chen's team for a formal design review. Reason: reduce impact before "
            "Software Integration. Affected area: Software Integration milestone.",
        ],
    )


def generate_meeting_minutes_02() -> None:
    _render(
        "meeting_minutes_02.pdf",
        "Meeting Minutes: Project Status Review, February 20, 2027",
        [
            "Attendees: Sofia Reyes, Elena Kovacs, Amara Osei.",
            "Decision: an alternate wiring harness subcontractor was approved to resolve the "
            "documentation gap described in RISK-003. Reason: unblock the FAA Compliance Review "
            "milestone. Affected area: FAA Compliance Review milestone.",
            "Decision: REQ-004 (night-vision-compatible display) will be deferred to a "
            "post-delivery software update due to continued supplier uncertainty (RISK-004). "
            "Reason: avoid delaying Final Delivery. Affected area: Requirements.",
        ],
    )


def generate_test_report() -> None:
    _render(
        "test_report.pdf",
        "Test Report: Aircraft Avionics Upgrade Project",
        [
            "TC-001 GPS accuracy bench test. Verifies REQ-001. Result: Pass. Measured accuracy "
            "1.4 meters CEP.",
            "TC-002 ARINC 429 bus interface test. Verifies REQ-002. Result: Pass.",
            "TC-003 Event logging timestamp precision test. Verifies REQ-003. Result: Pass. "
            "Measured precision 6 milliseconds.",
            "TC-004 Cold boot timing test. Verifies REQ-005. Result: Fail. Measured boot time 52 "
            "seconds, exceeding the 45 second requirement.",
        ],
    )


def generate_change_requests() -> None:
    _render(
        "change_requests.pdf",
        "Change Requests: Aircraft Avionics Upgrade Project",
        [
            "Decision: CR-014 was approved to review the cold boot timing threshold in REQ-005 "
            "after the TC-004 test failure. Reason: TC-004 measured 52 seconds against a 45 "
            "second requirement. Affected area: Requirements.",
        ],
    )


def generate_lessons_learned() -> None:
    _render(
        "lessons_learned.pdf",
        "Lessons Learned: Aircraft Avionics Upgrade Project",
        [
            "Risk observation: supplier lead-time visibility was insufficient during early "
            "procurement, which contributed to the GPS antenna delay described in RISK-001. "
            "Probability: High. Impact: High. Responsible: Procurement Team (Elena Kovacs).",
            "Decision: future projects should require suppliers to confirm manufacturing "
            "capacity before contract signature. Reason: prevent recurrence of RISK-001-style "
            "delays. Affected area: Procurement process.",
        ],
    )


def main() -> None:
    generate_project_charter()
    generate_requirements()
    generate_project_plan()
    generate_risk_register()
    generate_meeting_minutes_01()
    generate_meeting_minutes_02()
    generate_test_report()
    generate_change_requests()
    generate_lessons_learned()
    print(f"Generated 9 PDFs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
