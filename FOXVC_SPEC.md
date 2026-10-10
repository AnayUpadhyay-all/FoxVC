# FoxVC Language & Runtime Specification (Version 0.4.0)

FoxVC is a deterministic programming language featuring two unified native models:
1. **Relational Entity Space (RES):** 2D visual worlds governed by topological anchors, composition, and semantic relations instead of coordinate-based drawing commands.
2. **In-Memory Web Architecture:** Structural document models (FWEB), cascading visual rules (FSKIN), and reactive logic (FLOGIC) served in-memory over HTTP.

## 2D Relational Entity Space

### Directives:
* `space <Identifier>`: Defines an unbounded metric visual reference plane.
* `entity <Identifier>`: Declares a semantic visual unit with an intrinsic `form` (`circle`, `rect`, `polygon`, `arc`).
* `anchor <name> at <cardinal> [offset <x>, <y>]`: Declares custom points of interface relative to standard cardinal landmarks.
* `inside <Target> [at <Anchor>]`: Containment relation.
* `anchored_to <Target.Anchor> [at <Anchor>]`: Topological contact point alignment.
* `beside <Target> [direction <cardinal>] [spacing <N>]`: Cardinal proximity relation.
* `around <Target> distance <D> [bearing <Angle>]`: Polar orbital relationship.
* `connect <Name> from <A.anchor> to <B.anchor>`: Geometric connection spanning between two anchors.
* `replicate <N> of entity <Name> distributed [linear | radial | field]`: Generative spatial replication.
