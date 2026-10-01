from pathlib import Path
root=Path('.artifacts/diagnostic-source/src/aladdin/gem5')
h=root/'HybridDatapath.h'; s=h.read_text(); s=s.replace(' protected:\n', ''' protected:
  // Passive per-invocation diagnostics; never used by scheduling decisions.
  std::map<std::string, uint64_t> diagnosticCounts;
  std::set<unsigned> diagnosticSeenNodes;
  Tick diagnosticIssueBlockedTick = (Tick)-1;
  Tick diagnosticQueueBlockedTick = (Tick)-1;
  void diagnosticGraph(const std::string& stage);
  std::string diagnosticArray(ExecNode* node);
  void diagnosticRequest(const std::string& kind, unsigned node_id, bool load);
''',1); h.write_text(s)
p=root/'HybridDatapath.cpp'; s=p.read_text()
s=s.replace('  globalOptimizationPass();', '''  diagnosticCounts.clear();
  diagnosticSeenNodes.clear();
  diagnosticIssueBlockedTick = diagnosticQueueBlockedTick = (Tick)-1;
  diagnosticGraph("before");
  globalOptimizationPass();
  diagnosticGraph("after");''',1)
s=s.replace('  if (!cache_queue.canIssue()) {', '''  if (!cache_queue.canIssue()) {
    ++diagnosticCounts["issue_blocked_attempts"];
    if (diagnosticIssueBlockedTick != curTick()) {
      ++diagnosticCounts["issue_blocked_cycles"];
      diagnosticIssueBlockedTick = curTick();
    }''',1)
s=s.replace('  if (!entry)\n    entry = cache_queue.allocateEntry(vaddr, mem_access->size, isLoad);', '''  if (entry && diagnosticSeenNodes.insert(node_id).second)
    diagnosticRequest("queue_join_nodes", node_id, isLoad);
  if (!entry) {
    entry = cache_queue.allocateEntry(vaddr, mem_access->size, isLoad);
    if (entry) {
      diagnosticSeenNodes.insert(node_id);
      diagnosticRequest("queue_allocations", node_id, isLoad);
    }
  }''',1)
s=s.replace('  if (!entry) {\n    DPRINTF(HybridDatapathVerbose,', '''  if (!entry) {
    ++diagnosticCounts["queue_full_attempts"];
    if (diagnosticQueueBlockedTick != curTick()) {
      ++diagnosticCounts["queue_full_cycles"];
      diagnosticQueueBlockedTick = curTick();
    }
    DPRINTF(HybridDatapathVerbose,''',1)
s=s.replace('  if (!port.sendTimingReq(data_pkt)) {', '''  if (!port.sendTimingReq(data_pkt)) {
    if (op_type == Cache) diagnosticRequest("send_rejected", node_id, isLoad);''',1)
s=s.replace('  return Accepted;\n}\n\nHybridDatapath::IssueResult HybridDatapath::issueOwnershipRequest', '''  if (op_type == Cache) diagnosticRequest("accepted_initial", node_id, isLoad);
  return Accepted;
}

HybridDatapath::IssueResult HybridDatapath::issueOwnershipRequest''',1)
s=s.replace('      case Cache:\n        mem_stat_count', '''      case Cache:
        diagnosticRequest("returned", node_id, isLoad);
        mem_stat_count''',1)
s=s.replace('  MemoryQueueEntry* entry = cache_queue.findMatch(vaddr, isLoad);\n  panic_if(entry->status != Retry,', '''  if (mem_type == Cache && !state->is_ctrl_signal)
    diagnosticRequest("accepted_retry", state->node_id, isLoad);
  MemoryQueueEntry* entry = cache_queue.findMatch(vaddr, isLoad);
  panic_if(entry->status != Retry,''',1)
s=s.replace('void HybridDatapath::exitSimulation() {', '''void HybridDatapath::exitSimulation() {
  for (const auto& count : diagnosticCounts)
    std::cout << "DIAG request " << count.first << " " << count.second << std::endl;''',1)
s += '''
// Resolve arrays from recorded address ranges without changing graph labels.
std::string HybridDatapath::diagnosticArray(ExecNode* node) {
  if (node->get_mem_access()) {
    Addr addr = node->get_mem_access()->vaddr;
    for (const auto& part : user_params.partition)
      if (part.second.base_addr && addr >= part.second.base_addr &&
          addr - part.second.base_addr < part.second.array_size)
        return part.first;
  }
  // Mirror address-parent traversal read-only: pre-optimization load labels
  // are pointer temporaries until BaseAddressInit updates them.
  ExecNode* current = node;
  std::string label = current->get_array_label();
  auto edgeIds = get(boost::edge_name, program.graph);
  std::set<unsigned> visited;
  while (visited.insert(current->get_node_id()).second) {
    unsigned addressOperand = current->is_store_op() ? 2 : 1;
    ExecNode* parent = nullptr;
    in_edge_iter ei, end;
    for (boost::tie(ei, end) = in_edges(current->get_vertex(), program.graph);
         ei != end; ++ei)
      if (edgeIds[*ei] == addressOperand) {
        ExecNode* candidate = program.nodeAtVertex(source(*ei, program.graph));
        if (candidate->is_gep_op() || candidate->is_memory_op()) {
          parent = candidate; break;
        }
      }
    if (!parent) break;
    current = parent;
    label = current->get_array_label();
  }
  return label.empty() ? "unknown" : label;
}

void HybridDatapath::diagnosticRequest(const std::string& kind,
                                      unsigned node_id, bool load) {
  ++diagnosticCounts[kind + "." + diagnosticArray(program.nodes.at(node_id)) +
                     (load ? ".load" : ".store")];
}

void HybridDatapath::diagnosticGraph(const std::string& stage) {
  std::map<std::string, uint64_t> counts;
  std::set<unsigned> valueSlice;
  std::vector<unsigned> pending;
  auto edgeIds = get(boost::edge_name, program.graph);
  // C store value operands root the GEMM value slice; stop at loads so
  // address/index dependencies never become accumulation operations.
  for (const auto& pair : program.nodes) {
    ExecNode* node = pair.second;
    if (node->is_store_op() && diagnosticArray(node) == "C") {
      in_edge_iter ei, end;
      for (boost::tie(ei, end) = in_edges(node->get_vertex(), program.graph);
           ei != end; ++ei)
        if (edgeIds[*ei] == 1)
          pending.push_back(program.nodeAtVertex(source(*ei, program.graph))->get_node_id());
    }
  }
  while (!pending.empty()) {
    unsigned id = pending.back(); pending.pop_back();
    if (!valueSlice.insert(id).second) continue;
    ExecNode* node = program.nodes.at(id);
    if (node->is_memory_op() || node->is_gep_op()) continue;
    in_edge_iter ei, end;
    for (boost::tie(ei, end) = in_edges(node->get_vertex(), program.graph);
         ei != end; ++ei)
      if (edgeIds[*ei] != CONTROL_EDGE && edgeIds[*ei] != (uint8_t)MEMORY_EDGE)
        pending.push_back(program.nodeAtVertex(source(*ei, program.graph))->get_node_id());
  }
  for (const auto& pair : program.nodes) {
    ExecNode* node = pair.second;
    bool connected = boost::degree(node->get_vertex(), program.graph) > 0;
    std::string op = opcode_name(node->get_microop());
    if (node->is_memory_op())
      op += "." + diagnosticArray(node);
    if (node->get_microop() == LLVM_IR_Add || node->get_microop() == LLVM_IR_Mul)
      op += valueSlice.count(pair.first) ? ".gemm_value" : ".other";
    ++counts["all.nodes"];
    ++counts["all." + op];
    if (connected) {
      ++counts["connected.nodes"];
      ++counts["connected." + op];
    }
  }
  for (const auto& count : counts)
    std::cout << "DIAG graph " << stage << " " << count.first << " "
              << count.second << std::endl;
}
'''
p.write_text(s)
