Fetch the user's Phras style prompt and apply it to this conversation.

**Arguments:** $ARGUMENTS
Parse as `[formality] [context]` — both optional.
- formality: `no_censor` | `casual` | `family` | `semi_formal` | `formal` — default: `semi_formal`
- context: `general` | `email` | `reply` | `tweet` | `linkedin` — default: `general`

**Steps:**

1. Parse $ARGUMENTS to extract formality and context, using the defaults above if not provided.

2. Check that the environment variables `PHRAS_API_KEY` and `PHRAS_STYLE_ID` are set. If either is missing, tell the user to run these commands and then retry:
   ```
   claude config set env.PHRAS_API_KEY phr_your_key_here
   claude config set env.PHRAS_STYLE_ID your_style_id_here
   ```
   Then stop.

3. Use the Bash tool to call the Phras API, substituting the actual formality and context values from step 1:
   ```bash
   curl.exe -s "https://phras.onrender.com/v1/style/${PHRAS_STYLE_ID}?formality=FORMALITY&context=CONTEXT" -H "X-API-Key: ${PHRAS_API_KEY}"
   ```
   On Mac/Linux use `curl` instead of `curl.exe`.

4. Parse the JSON response and extract `constraint.system_prompt`.

5. Display the system prompt to the user in a code block so they can copy it for use elsewhere.

6. Apply those style constraints to every response you give for the rest of this conversation — write in the user's voice as described by the system prompt.
