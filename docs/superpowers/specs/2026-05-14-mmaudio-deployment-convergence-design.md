# MMAudio Deployment Convergence Design

## Goal

Converge the `192.168.100.19` deployment back to the standard MMAudio deployment shape so both production instances register as the same logical service:

- container name: `mmaudio`
- caddy hosts: `mmaudio`, `mmaudio-api`

The old `shared-smartmodel-gpu1` naming is treated as incorrect state and will be removed instead of maintained.

## Desired End State

Two hosts run the same MMAudio service definition and the same published image.

- `ttd-worker`
  - container name: `mmaudio`
  - caddy labels: `mmaudio:80, mmaudio-api:80`
  - service port in container: `7860`
- `192.168.100.19`
  - container name: `mmaudio`
  - caddy labels: `mmaudio:80, mmaudio-api:80`
  - service port in container: `7860`

Host-level differences remain configuration only:

- target machine
- GPU id
- published host port if needed for direct host access

CDP is expected to aggregate multiple registrations for the same caddy host and expose them as multiple upstream backends under `mmaudio` and `mmaudio-api`.

## Scope

In scope:

- remove the special-case `shared-smartmodel-gpu1` container/domain naming from deployment operations
- make repository deployment docs and inventory match the standard `mmaudio` naming
- redeploy `192.168.100.19` with the standard compose definition
- verify that the ingress layer sees two real backends for `mmaudio` and two for `mmaudio-api`

Out of scope:

- changing MMAudio application behavior
- changing image build contents
- introducing manual caddy config patches
- keeping compatibility aliases for `mmaudio-shared-smartmodel-gpu1`

## Approaches Considered

### Approach 1: Full convergence now

Redeploy `192.168.100.19` using the same service name, container name, and caddy labels as the standard deployment, then verify that CDP aggregates both instances under the same hostnames.

Pros:

- matches the intended final state immediately
- removes the wrong naming instead of preserving it
- keeps the repo as the single source of truth

Cons:

- depends on ingress aggregation working exactly as expected

Recommendation: use this approach.

### Approach 2: Temporary dual naming

Keep the old GPU1-specific names while adding the standard names during a transition period.

Pros:

- lower immediate rollback pressure

Cons:

- preserves known-wrong declarations
- leaves ambiguity in operations and documentation

Rejected because the user explicitly does not want to continue maintaining the wrong declaration.

## Design

### Deployment configuration

`compose.deploy.yaml` remains the only formal runtime declaration. It already encodes the desired steady-state service shape:

- service name `mmaudio`
- `container_name: mmaudio`
- caddy labels `mmaudio` and `mmaudio-api`

Machine-specific overrides must not rename the service or change caddy hostnames. They may only vary runtime parameters such as GPU id and published host port.

### Remote host normalization

`192.168.100.19` must be normalized so it is launched from the standard `compose.deploy.yaml` contract rather than any local GPU1-specific override that changes naming.

Required cleanup:

- stop using `mmaudio-shared-smartmodel-gpu1` as a container name
- stop advertising `mmaudio-shared-smartmodel-gpu1` and `mmaudio-shared-smartmodel-gpu1-api`
- remove or stop using the local override files that encoded that naming

### Ingress behavior

Both hosts will advertise the same two caddy hostnames:

- `mmaudio`
- `mmaudio-api`

Expected ingress result:

- `mmaudio` has two upstream backends
- `mmaudio-api` has two upstream backends

This is verified from the live `caddy-docker-proxy` admin config rather than assumed from labels alone.

## Verification Plan

After redeployment, verify all of the following:

1. On `ttd-worker`, `docker inspect mmaudio` succeeds and the running image is the expected MMAudio image.
2. On `192.168.100.19`, `docker inspect mmaudio` succeeds and there is no active `mmaudio-shared-smartmodel-gpu1` container.
3. `GET /health` succeeds through direct host access where applicable.
4. `GET /` returns the Gradio homepage for the unified deployment.
5. `POST /api/v1/text-to-audio` returns `audio/wav` with `RIFF` output.
6. Live Caddy admin config shows:
   - `host = mmaudio` with two upstream dials
   - `host = mmaudio-api` with two upstream dials

## Risks and Handling

### Risk: old local override keeps winning

Handling:

- inspect the actual remote compose invocation path
- stop using any override that changes service naming
- verify the live container name after deployment rather than trusting deploy logs

### Risk: ingress only registers one instance

Handling:

- inspect live Caddy admin config for upstream count
- if only one backend appears, stop and diagnose service discovery instead of keeping mixed naming

### Risk: direct host port differences cause confusion

Handling:

- treat host port as an operational detail only
- use caddy hostnames as the canonical user-facing access path

## Implementation Notes

Expected repository changes are limited to deployment-facing files and docs, not application code. Likely touch points:

- `ansible/inventory.yml`
- deployment docs if they still mention the GPU1-specific aliasing

Remote operational cleanup may include deleting or ignoring local files that were created only for the wrong GPU1-specific deployment path.
