export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  avatarUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Business {
  id: string;
  userId: string;
  name: string;
  industry: string;
  legalStructure: "sole_proprietorship" | "partnership" | "llp" | "private_limited" | "huf";
  country: string;
  state: string;
  gstin?: string;
  pan?: string;
  udyam?: string;
  turnover: number;
  employeeCount: number;
  bankingRelationships: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Invoice {
  id: string;
  userId: string;
  businessId: string;
  invoiceNumber: string;
  clientName: string;
  clientGstin?: string;
  amount: number;
  taxAmount: number;
  totalAmount: number;
  date: string;
  dueDate: string;
  status: "draft" | "sent" | "paid" | "overdue" | "cancelled";
  fileUrl?: string;
  ocrData?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Expense {
  id: string;
  userId: string;
  businessId: string;
  amount: number;
  category: string;
  subcategory?: string;
  vendorName?: string;
  gstin?: string;
  description: string;
  date: string;
  isGstEligible: boolean;
  itcClaimed: boolean;
  fileUrl?: string;
  ocrData?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface TaxPayment {
  id: string;
  userId: string;
  businessId: string;
  type: "income_tax" | "tds" | "advance_tax" | "gc";
  amount: number;
  dueDate: string;
  paidDate?: string;
  status: "pending" | "paid" | "overdue";
  challanNumber?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ComplianceTask {
  id: string;
  userId: string;
  businessId: string;
  title: string;
  description: string;
  type: "gstr" | "tds" | "pf" | "esi" | "income_tax" | "roc" | "labour" | "import_export";
  dueDate: string;
  status: "upcoming" | "in_progress" | "completed" | "overdue";
  reminderDays: number[];
  createdAt: string;
  updatedAt: string;
}

export interface FinancialForecast {
  id: string;
  userId: string;
  businessId: string;
  period: "30d" | "90d" | "180d" | "365d";
  projectedRevenue: number;
  projectedExpenses: number;
  projectedProfit: number;
  projectedTax: number;
  confidenceScore: number;
  dataPoints: { month: string; revenue: number; expenses: number }[];
  createdAt: string;
}

export interface AuditFinding {
  id: string;
  userId: string;
  businessId: string;
  type: "duplicate_invoice" | "missing_receipt" | "tax_mismatch" | "unusual_expense" | "vendor_risk";
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  amountAtRisk?: number;
  status: "open" | "resolved" | "false_positive";
  llmAnalysis?: string;
  createdAt: string;
  resolvedAt?: string;
}

export interface Document {
  id: string;
  userId: string;
  businessId: string;
  filename: string;
  fileUrl: string;
  fileType: string;
  fileSize: number;
  category: "invoice" | "expense" | "tax" | "legal" | "other";
  ocrData?: Record<string, any>;
  tags: string[];
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  userId: string;
  sessionId: string;
  role: "user" | "assistant";
  content: string;
  module?: string;
  sources?: string[];
  createdAt: string;
}
