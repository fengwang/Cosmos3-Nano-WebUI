# Exclusion Manifest Specification

## ADDED Requirements

### Requirement: Default Exclusions

The session SHALL define exclusions for model weights, generated media, archives, caches, bulky evidence, temporary folders, local-only outputs, private evidence, secrets, and legacy submodules.

#### Scenario: Weight Or Media Candidate

WHEN a future import contains files ending in `.safetensors`, `.pt`, `.pth`, `.ckpt`, `.mp4`, `.mov`, or `.avi`
THEN `docs/session_1/exclusion_manifest.md` MUST require exclusion by default and owner review before any exception.

#### Scenario: Cache Or Archive Candidate

WHEN a future import contains cache folders, archive files, or bulky generated evidence
THEN `docs/session_1/exclusion_manifest.md` MUST require exclusion unless a later contract explicitly allows it.

### Requirement: Legacy Submodule Exclusion

The session SHALL require legacy plain vLLM and TensorRT-LLM submodules to stay out of the first milestone unless a later session proves a public runtime need.

#### Scenario: Legacy Submodule Reference

WHEN a future import includes `submodules/vllm`, `TensorRT-LLM`, or equivalent legacy dependency paths
THEN `docs/session_1/exclusion_manifest.md` MUST require the future worker to stop, classify the need, and obtain a contract-level decision before import.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
