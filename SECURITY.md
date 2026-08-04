# Security policy

## Supported versions

Vyuha is a research and coursework project under active development. Security fixes are
applied to the latest `main`. Older tags are not maintained.

| Version | Supported |
|---------|-----------|
| latest `main` | yes |
| older tags | no |

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private reporting:
open the repository's **Security** tab and choose **Report a vulnerability** (private
security advisory). Include a description, affected files or endpoints, and steps to
reproduce.

I aim to acknowledge a report within a few days and to agree on a disclosure timeline once
the issue is confirmed. Because this is a student-maintained project, please allow
reasonable time before any public disclosure.

## Scope

In scope: the Vyuha library, the evaluation harness, and the FastAPI service in this
repository. A useful report shows a concrete bypass of a defense layer, a false decision
with security impact, or a flaw in the service (for example, an injection or an unsafe
default).

Out of scope: findings that require a compromised host or dependency, denial of service
from unrealistic input sizes, and the inherent fact that no single detector is perfect.
Adversarial evasions that beat a layer are expected and welcome as issues or pull requests,
since improving them is the whole point of Vyuha.

## Safe harbor

Good-faith security research on your own instance, without accessing others' data or
degrading service, is welcome and will not be pursued.
