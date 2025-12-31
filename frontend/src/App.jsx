import { useState, useEffect } from "react";
import axios from "axios";
import "./index.css";

const API_BASE = "/api/rest";

function App() {
  const [activeTab, setActiveTab] = useState("tenant");
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [inspectingInvoice, setInspectingInvoice] = useState(null);
  const [matchedTransaction, setMatchedTransaction] = useState(null);
  const [matchExplanations, setMatchExplanations] = useState({});

  // Form states
  const [tenantName, setTenantName] = useState("");
  const [invoiceForm, setInvoiceForm] = useState({
    amount: "",
    currency: "USD",
    invoice_number: "",
    description: "",
    invoice_date: new Date().toISOString().split("T")[0],
  });
  const [transactionForm, setTransactionForm] = useState({
    external_id: "",
    posted_at: new Date().toISOString().split("T")[0] + "T10:00:00Z",
    amount: "",
    currency: "USD",
    description: "",
  });

  useEffect(() => {
    loadTenants();
  }, []);

  useEffect(() => {
    if (selectedTenant) {
      loadInvoices();
      loadTransactions();
      loadMatches();
    }
  }, [selectedTenant]);

  const showMessage = (text, type = "success") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const loadTenants = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tenants`);
      setTenants(res.data.tenants);
      if (res.data.tenants.length > 0 && !selectedTenant) {
        setSelectedTenant(res.data.tenants[0].id);
      }
    } catch (error) {
      showMessage("Failed to load tenants", "error");
    }
  };

  const createTenant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/tenants`, { name: tenantName });
      showMessage("Tenant created successfully!");
      setTenantName("");
      await loadTenants();
      setSelectedTenant(res.data.id);
    } catch (error) {
      showMessage("Failed to create tenant", "error");
    } finally {
      setLoading(false);
    }
  };

  const loadInvoices = async () => {
    if (!selectedTenant) return;
    try {
      const res = await axios.get(
        `${API_BASE}/tenants/${selectedTenant}/invoices`
      );
      setInvoices(res.data.invoices);
    } catch (error) {
      showMessage("Failed to load invoices", "error");
    }
  };

  const createInvoice = async (e) => {
    e.preventDefault();
    if (!selectedTenant) {
      showMessage("Please select a tenant first", "error");
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/tenants/${selectedTenant}/invoices`, {
        ...invoiceForm,
        amount: parseFloat(invoiceForm.amount),
      });
      showMessage("Invoice created successfully!");
      setInvoiceForm({
        amount: "",
        currency: "USD",
        invoice_number: "",
        description: "",
        invoice_date: new Date().toISOString().split("T")[0],
      });
      await loadInvoices();
    } catch (error) {
      showMessage("Failed to create invoice", "error");
    } finally {
      setLoading(false);
    }
  };

  const deleteInvoice = async (id) => {
    if (!confirm("Are you sure you want to delete this invoice?")) return;
    try {
      await axios.delete(
        `${API_BASE}/tenants/${selectedTenant}/invoices/${id}`
      );
      showMessage("Invoice deleted successfully!");
      await loadInvoices();
    } catch (error) {
      showMessage("Failed to delete invoice", "error");
    }
  };

  const importTransaction = async (e) => {
    e.preventDefault();
    if (!selectedTenant) {
      showMessage("Please select a tenant first", "error");
      return;
    }
    setLoading(true);
    try {
      await axios.post(
        `${API_BASE}/tenants/${selectedTenant}/bank-transactions/import`,
        {
          transactions: [
            {
              ...transactionForm,
              amount: parseFloat(transactionForm.amount),
            },
          ],
        },
        {
          headers: {
            "X-Idempotency-Key": `import-${Date.now()}`,
          },
        }
      );
      showMessage("Transaction imported successfully!");
      setTransactionForm({
        external_id: "",
        posted_at: new Date().toISOString().split("T")[0] + "T10:00:00Z",
        amount: "",
        currency: "USD",
        description: "",
      });
      await loadTransactions();
    } catch (error) {
      if (error.response && error.response.status === 409) {
        showMessage(
          "Duplicate details detected. This transaction has already been imported.",
          "error"
        );
      } else {
        showMessage("Failed to import transaction", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteTransaction = async (id) => {
    if (!confirm("Are you sure you want to delete this bank transaction?"))
      return;
    try {
      await axios.delete(
        `${API_BASE}/tenants/${selectedTenant}/bank-transactions/${id}`
      );
      showMessage("Transaction deleted successfully!");
      await loadTransactions();
    } catch (error) {
      showMessage("Failed to delete transaction", "error");
    }
  };

  const inspectMatch = async (invoiceId) => {
    try {
      const res = await axios.get(
        `${API_BASE}/tenants/${selectedTenant}/invoices/${invoiceId}/match`
      );
      if (res.data) {
        const matchData = res.data;
        const tx = transactions.find(
          (t) => t.id === matchData.bank_transaction_id
        );
        if (tx) {
          setMatchedTransaction(tx);
          setInspectingInvoice(invoices.find((i) => i.id === invoiceId));
        } else {
          showMessage("Matched transaction details not found in list", "error");
        }
      }
    } catch (error) {
      showMessage("Failed to load match details", "error");
    }
  };

  const runReconciliation = async () => {
    if (!selectedTenant) {
      showMessage("Please select a tenant first", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(
        `${API_BASE}/tenants/${selectedTenant}/reconcile?min_score=50.0`
      );
      showMessage(`Reconciliation complete! Found ${res.data.count} matches.`);
      await loadMatches();
      await loadInvoices();
    } catch (error) {
      showMessage("Failed to run reconciliation", "error");
    } finally {
      setLoading(false);
    }
  };

  const loadMatches = async () => {
    if (!selectedTenant) return;
    try {
      const res = await axios.get(
        `${API_BASE}/tenants/${selectedTenant}/reconcile/candidates`
      );
      setMatches(res.data.matches || []);
    } catch (error) {
      // Ignore if no matches yet
    }
  };

  const loadTransactions = async () => {
    if (!selectedTenant) return;
    try {
      const res = await axios.get(
        `${API_BASE}/tenants/${selectedTenant}/bank-transactions`
      );
      setTransactions(res.data.transactions);
    } catch (error) {
      showMessage("Failed to load transactions", "error");
    }
  };

  const confirmMatch = async (matchId) => {
    if (!confirm("Confirm this match?")) return;
    try {
      await axios.post(
        `${API_BASE}/tenants/${selectedTenant}/matches/${matchId}/confirm`
      );
      showMessage("Match confirmed successfully!");
      await loadMatches();
      await loadInvoices();
    } catch (error) {
      showMessage("Failed to confirm match", "error");
    }
  };

  const getExplanation = async (invoiceId, transactionId) => {
    try {
      const res = await axios.get(
        `${API_BASE}/tenants/${selectedTenant}/reconcile/explain`,
        { params: { invoice_id: invoiceId, transaction_id: transactionId } }
      );
      return res.data;
    } catch (error) {
      return { explanation: "Explanation unavailable", confidence: "low" };
    }
  };

  const getScoreClass = (score) => {
    if (score >= 80) return "score-high";
    if (score >= 50) return "score-medium";
    return "score-low";
  };

  return (
    <div className="container">
      <h1>🧾 Invoice Reconciliation System</h1>

      {message && (
        <div className={`alert alert-${message.type}`}>{message.text}</div>
      )}

      <div className="card">
        <h3>Select Tenant</h3>
        <select
          value={selectedTenant || ""}
          onChange={(e) => setSelectedTenant(Number(e.target.value))}
          style={{ marginBottom: "15px" }}
        >
          <option value="">-- Select Tenant --</option>
          {tenants.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        {selectedTenant && (
          <p style={{ color: "#9ca3af" }}>
            Working with:{" "}
            <strong style={{ color: "#f9fafb" }}>
              {tenants.find((t) => t.id === selectedTenant)?.name}
            </strong>
          </p>
        )}
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === "tenant" ? "active" : ""}`}
          onClick={() => setActiveTab("tenant")}
        >
          Tenants
        </button>
        <button
          className={`tab ${activeTab === "invoice" ? "active" : ""}`}
          onClick={() => setActiveTab("invoice")}
          disabled={!selectedTenant}
        >
          Invoices
        </button>
        <button
          className={`tab ${activeTab === "transactions" ? "active" : ""}`}
          onClick={() => setActiveTab("transactions")}
          disabled={!selectedTenant}
        >
          Transactions
        </button>
        <button
          className={`tab ${activeTab === "reconcile" ? "active" : ""}`}
          onClick={() => setActiveTab("reconcile")}
          disabled={!selectedTenant}
        >
          Reconciliation
        </button>
      </div>

      {/* Tenants Tab */}
      <div className={`tab-content ${activeTab === "tenant" ? "active" : ""}`}>
        <div className="card">
          <h2>Create Tenant</h2>
          <form onSubmit={createTenant}>
            <div className="form-group">
              <label>Tenant Name</label>
              <input
                type="text"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                required
                placeholder="e.g., Acme Corp"
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Tenant"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>All Tenants</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.name}</td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoices Tab */}
      <div className={`tab-content ${activeTab === "invoice" ? "active" : ""}`}>
        <div className="card">
          <h2>Create Invoice</h2>
          <form onSubmit={createInvoice}>
            <div className="grid">
              <div className="form-group">
                <label>Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={invoiceForm.amount}
                  onChange={(e) =>
                    setInvoiceForm({ ...invoiceForm, amount: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <select
                  value={invoiceForm.currency}
                  onChange={(e) =>
                    setInvoiceForm({ ...invoiceForm, currency: e.target.value })
                  }
                >
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </div>
              <div className="form-group">
                <label>Invoice Number</label>
                <input
                  type="text"
                  value={invoiceForm.invoice_number}
                  onChange={(e) =>
                    setInvoiceForm({
                      ...invoiceForm,
                      invoice_number: e.target.value,
                    })
                  }
                  placeholder="e.g., INV-001"
                />
              </div>
              <div className="form-group">
                <label>Invoice Date</label>
                <input
                  type="date"
                  value={invoiceForm.invoice_date}
                  onChange={(e) =>
                    setInvoiceForm({
                      ...invoiceForm,
                      invoice_date: e.target.value,
                    })
                  }
                />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={invoiceForm.description}
                onChange={(e) =>
                  setInvoiceForm({
                    ...invoiceForm,
                    description: e.target.value,
                  })
                }
                rows="3"
                placeholder="Invoice description"
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Invoice"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Invoices ({invoices.length})</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Number</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.id}</td>
                  <td>{inv.invoice_number || "N/A"}</td>
                  <td>
                    ${parseFloat(inv.amount).toFixed(2)} {inv.currency}
                  </td>
                  <td>
                    {inv.invoice_date
                      ? new Date(inv.invoice_date).toLocaleDateString()
                      : "N/A"}
                  </td>
                  <td>
                    <span
                      className={`badge badge-${
                        inv.status === "matched"
                          ? "success"
                          : inv.status === "open"
                          ? "warning"
                          : "info"
                      }`}
                    >
                      {inv.status}
                    </span>
                  </td>
                  <td>
                    {inv.status === "matched" && (
                      <button
                        className="btn-secondary btn-small"
                        onClick={() => inspectMatch(inv.id)}
                        style={{ marginRight: "5px" }}
                      >
                        Inspect
                      </button>
                    )}
                    <button
                      className="btn-danger btn-small"
                      onClick={() => deleteInvoice(inv.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transactions Tab */}
      <div
        className={`tab-content ${
          activeTab === "transactions" ? "active" : ""
        }`}
      >
        <div className="card">
          <h2>Import Bank Transaction</h2>
          <form onSubmit={importTransaction}>
            <div className="grid">
              <div className="form-group">
                <label>External ID</label>
                <input
                  type="text"
                  value={transactionForm.external_id}
                  onChange={(e) =>
                    setTransactionForm({
                      ...transactionForm,
                      external_id: e.target.value,
                    })
                  }
                  placeholder="e.g., TXN-001"
                />
              </div>
              <div className="form-group">
                <label>Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={transactionForm.amount}
                  onChange={(e) =>
                    setTransactionForm({
                      ...transactionForm,
                      amount: e.target.value,
                    })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <select
                  value={transactionForm.currency}
                  onChange={(e) =>
                    setTransactionForm({
                      ...transactionForm,
                      currency: e.target.value,
                    })
                  }
                >
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </div>
              <div className="form-group">
                <label>Posted Date</label>
                <input
                  type="datetime-local"
                  value={transactionForm.posted_at
                    .replace("Z", "")
                    .slice(0, 16)}
                  onChange={(e) =>
                    setTransactionForm({
                      ...transactionForm,
                      posted_at: e.target.value + ":00Z",
                    })
                  }
                  required
                />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={transactionForm.description}
                onChange={(e) =>
                  setTransactionForm({
                    ...transactionForm,
                    description: e.target.value,
                  })
                }
                rows="3"
                placeholder="Transaction description"
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? "Importing..." : "Import Transaction"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Bank Transactions ({transactions.length})</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Ext ID</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>{tx.id}</td>
                  <td>{tx.external_id || "N/A"}</td>
                  <td>
                    ${parseFloat(tx.amount).toFixed(2)} {tx.currency}
                  </td>
                  <td>
                    {tx.posted_at
                      ? new Date(tx.posted_at).toLocaleDateString()
                      : "N/A"}
                  </td>
                  <td>{tx.description || "N/A"}</td>
                  <td>
                    <button
                      className="btn-danger btn-small"
                      onClick={() => deleteTransaction(tx.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td
                    colSpan="6"
                    style={{
                      textAlign: "center",
                      padding: "20px",
                      color: "#9ca3af",
                    }}
                  >
                    No transactions found. Use the form above to import one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reconciliation Tab */}
      <div
        className={`tab-content ${activeTab === "reconcile" ? "active" : ""}`}
      >
        <div className="card">
          <h2>Run Reconciliation</h2>
          <p style={{ marginBottom: "15px", color: "#9ca3af" }}>
            This will automatically match invoices to bank transactions based on
            amount, date, and description similarity.
          </p>
          <button
            onClick={runReconciliation}
            disabled={loading || invoices.length === 0}
            className="btn-success"
          >
            {loading ? "Running..." : "Run Reconciliation"}
          </button>
        </div>

        <div className="card">
          <h2>Match Candidates ({matches.length})</h2>
          {matches.length === 0 ? (
            <p
              style={{ color: "#9ca3af", textAlign: "center", padding: "20px" }}
            >
              No matches found. Run reconciliation first or create invoices and
              transactions.
            </p>
          ) : (
            <div className="grid">
              {matches.map((match) => {
                const invoice = invoices.find((i) => i.id === match.invoice_id);
                return (
                  <div
                    key={match.id}
                    className={`match-card ${
                      match.status === "confirmed" ? "confirmed" : ""
                    }`}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "10px",
                      }}
                    >
                      <h3>Match #{match.id}</h3>
                      <span
                        className={`score ${getScoreClass(
                          parseFloat(match.score)
                        )}`}
                      >
                        Score: {parseFloat(match.score).toFixed(1)}/100
                      </span>
                    </div>
                    <p>
                      <strong>Invoice:</strong>{" "}
                      {invoice?.invoice_number || `#${match.invoice_id}`} - $
                      {parseFloat(invoice?.amount || 0).toFixed(2)}
                    </p>
                    <p>
                      <strong>Transaction:</strong> #{match.bank_transaction_id}
                    </p>
                    <p>
                      <strong>Status:</strong>
                      <span
                        className={`badge badge-${
                          match.status === "confirmed" ? "success" : "warning"
                        }`}
                      >
                        {match.status}
                      </span>
                    </p>
                    {match.status === "proposed" && (
                      <div style={{ marginTop: "15px" }}>
                        <button
                          className="btn-success btn-small"
                          onClick={() => confirmMatch(match.id)}
                          style={{ marginRight: "10px" }}
                        >
                          Confirm Match
                        </button>
                        <button
                          className="btn-secondary btn-small"
                          onClick={async () => {
                            const res = await getExplanation(
                              match.invoice_id,
                              match.bank_transaction_id
                            );
                            setMatchExplanations((prev) => ({
                              ...prev,
                              [match.id]: res,
                            }));
                          }}
                        >
                          {matchExplanations[match.id]
                            ? "Refresh Explanation"
                            : "Get Explanation"}
                        </button>
                      </div>
                    )}
                    {matchExplanations[match.id] && (
                      <div
                        className="explanation-box"
                        style={{ marginTop: "15px", fontSize: "0.9rem" }}
                      >
                        <p>{matchExplanations[match.id].explanation}</p>
                        <span
                          className={`confidence confidence-${
                            matchExplanations[match.id].confidence
                          }`}
                        >
                          Confidence: {matchExplanations[match.id].confidence}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      {inspectingInvoice && matchedTransaction && (
        <div
          className="modal-overlay"
          onClick={() => setInspectingInvoice(null)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Matched Transaction Details</h2>
              <button
                className="close-button"
                onClick={() => setInspectingInvoice(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div
                className="card"
                style={{ background: "#4b5563", marginBottom: "0" }}
              >
                <h3>Invoice #{inspectingInvoice.invoice_number}</h3>
                <p>
                  <strong>Amount:</strong> $
                  {parseFloat(inspectingInvoice.amount).toFixed(2)}{" "}
                  {inspectingInvoice.currency}
                </p>
                <p>
                  <strong>Date:</strong>{" "}
                  {new Date(
                    inspectingInvoice.invoice_date
                  ).toLocaleDateString()}
                </p>
                <p>
                  <strong>Description:</strong>{" "}
                  {inspectingInvoice.description || "N/A"}
                </p>
              </div>

              <div
                style={{
                  textAlign: "center",
                  margin: "15px 0",
                  fontSize: "24px",
                }}
              >
                🔗
              </div>

              <div
                className="card"
                style={{ background: "#065f46", marginBottom: "0" }}
              >
                <h3>Matched Bank Transaction</h3>
                <p>
                  <strong>ID:</strong> {matchedTransaction.id}
                </p>
                <p>
                  <strong>Ext ID:</strong>{" "}
                  {matchedTransaction.external_id || "N/A"}
                </p>
                <p>
                  <strong>Amount:</strong> $
                  {parseFloat(matchedTransaction.amount).toFixed(2)}{" "}
                  {matchedTransaction.currency}
                </p>
                <p>
                  <strong>Date:</strong>{" "}
                  {new Date(matchedTransaction.posted_at).toLocaleDateString()}
                </p>
                <p>
                  <strong>Description:</strong>{" "}
                  {matchedTransaction.description || "N/A"}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
