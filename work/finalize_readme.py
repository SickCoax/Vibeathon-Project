from pathlib import Path
p=Path('README.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('## Local-only / external capabilities', '## Run provider tests\n\nRun `python -m unittest tests.test_provider -v`. The tests mock provider responses to verify endpoint JSON and error handling. They do not make a real Gemini request. A successful live transformation requires your own API key.\n\n## Local-only / external capabilities')
s=s.replace('- Text rewrite requires a configured provider key and may incur usage charges.', '- Text rewrite requires a Gemini API key. `gemini-3.5-flash-lite` is listed as free-tier for text input/output at the time this README was updated; quota and access can vary by region/project. No billing is enabled by this app.')
s=s.replace('No automated test suite is bundled in this initial version.', 'The provider endpoint tests use mocked HTTP responses; no live-provider inference test runs without a user-supplied key.')
p.write_text(s,encoding='utf-8')
