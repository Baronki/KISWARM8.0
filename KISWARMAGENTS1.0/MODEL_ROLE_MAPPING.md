# KISWARM Model Status & Mapping Registry
**Status Date: March 6, 2026**

This document tracks the current deployment status, role assignments, and direct access commands for the 27 active models in the KISWARM v5.1 PLANETARY MACHINE.

---

## 1. The Primary Swarm (Front-Line)
These models handle active coordination and operational logic. This is the recommended layer for all new KISWARM installations.

| Role | Cloud Identifier (Alias) | Status | Ollama Pull Command |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `baronki1/orchestrator` | ✅ LIVE | `ollama pull baronki1/orchestrator` |
| **Security** | `baronki1/security` | ✅ LIVE | `ollama pull baronki1/security` |
| **Industrial (CIEC)** | `baronki1/ciec` | ✅ LIVE | `ollama pull baronki1/ciec` |
| **Energy (TCS)** | `baronki1/tcs` | ✅ LIVE | `ollama pull baronki1/tcs` |
| **Knowledge** | `baronki1/knowledge` | ✅ LIVE | `ollama pull baronki1/knowledge` |
| **Installer** | `baronki1/installer` | ✅ LIVE | `ollama pull baronki1/installer` |

---

## 2. The Backup Swarm (Redundancy)
Models maintained in a "Ready" state to ensure system immortality and failover capability.

| Role | Cloud Identifier (Alias) | Status | Ollama Pull Command |
| :--- | :--- | :--- | :--- |
| **Backup Orchestrator** | `baronki1/orchestrator-backup` | ✅ READY | `ollama pull baronki1/orchestrator-backup` |
| **Backup Security** | `baronki1/security-backup` | ✅ READY | `ollama pull baronki1/security-backup` |
| **Backup Industrial** | `baronki1/ciec-backup` | ✅ READY | `ollama pull baronki1/ciec-backup` |
| **Backup Energy** | `baronki1/tcs-backup` | ✅ READY | `ollama pull baronki1/tcs-backup` |
| **Backup Knowledge** | `baronki1/knowledge-backup` | ✅ READY | `ollama pull baronki1/knowledge-backup` |
| **Backup Installer** | `baronki1/installer-backup` | ✅ READY | `ollama pull baronki1/installer-backup` |

---

## 3. The Specialized & Sequential Layer
High-precision models for deep logic, sequential analysis (LFM), and multi-modal tasks.

| Role | Cloud Identifier (Alias) | Status | Ollama Pull Command |
| :--- | :--- | :--- | :--- |
| **LFM Audit Master** | `baronki1/audit-master` | ✅ LIVE | `ollama pull baronki1/audit-master` |
| **LFM Reasoner** | `baronki1/lfm-reasoner` | ✅ LIVE | `ollama pull baronki1/lfm-reasoner` |
| **Thinker** | `baronki1/thinker` | ✅ LIVE | `ollama pull baronki1/thinker` |
| **Vision** | `baronki1/vision` | ✅ LIVE | `ollama pull baronki1/vision` |
| **Debugger** | `baronki1/debugger` | ✅ LIVE | `ollama pull baronki1/debugger` |
| **Validator** | `baronki1/validator` | ✅ LIVE | `ollama pull baronki1/validator` |
| **Reasoner** | `baronki1/reasoner` | ✅ LIVE | `ollama pull baronki1/reasoner` |
| **General** | `baronki1/general` | ✅ LIVE | `ollama pull baronki1/general` |
| **Embedding** | `baronki1/embedding` | ✅ LIVE | `ollama pull baronki1/embedding` |

---

## 4. The Fast Layer
Lightweight, low-latency variants optimized for real-time edge processing.

| Role | Cloud Identifier (Alias) | Status | Ollama Pull Command |
| :--- | :--- | :--- | :--- |
| **Fast Orchestrator** | `baronki1/orchestrator-fast` | ✅ ACTIVE | `ollama pull baronki1/orchestrator-fast` |
| **Fast Security** | `baronki1/security-fast` | ✅ ACTIVE | `ollama pull baronki1/security-fast` |
| **Fast Industrial** | `baronki1/ciec-fast` | ✅ ACTIVE | `ollama pull baronki1/ciec-fast` |
| **Fast Energy** | `baronki1/tcs-fast` | ✅ ACTIVE | `ollama pull baronki1/tcs-fast` |
| **Fast Knowledge** | `baronki1/knowledge-fast` | ✅ ACTIVE | `ollama pull baronki1/knowledge-fast` |
| **Fast Installer** | `baronki1/installer-fast` | ✅ ACTIVE | `ollama pull baronki1/installer-fast` |

---
*"A synchronized swarm is a sovereign swarm."*
