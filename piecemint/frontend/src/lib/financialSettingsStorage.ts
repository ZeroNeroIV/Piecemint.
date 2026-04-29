import { getItemMigrated, setItemMigrated } from './localStorageScope';

const STORAGE_KEY = 'ff_financial_settings_v1';

export type FinancialSettings = {
  businessName: string;
  taxId: string;
  address: string;
  baseCurrency: string;
  fiscalYearStartMonth: string;
  fiscalYearStartDay: string;
  timezone: string;
  dateFormat: string;
  taxDefaultRate: string;
  taxCustomRules: string;
  taxInclusivePricing: boolean;
  taxExemptions: string;
  taxBufferPercent: string;
  linkedAccounts: string;
  paymentMethods: string;
  payoutSchedule: string;
  passTransactionFees: boolean;
  invoiceLogoUrl: string;
  invoicePrimaryColor: string;
  invoiceFont: string;
  invoicePrefix: string;
  invoiceNumberStart: string;
  invoiceDefaultTermsDays: string;
  invoiceLateFeePolicy: string;
  invoiceAutomatedReminders: boolean;
  chartOfAccountsCategories: string;
  receiptRules: string;
  ocrEnabled: boolean;
  mileageRate: string;
  dataExportOptions: string;
  auditLogsSummary: string;
  approvalWorkflowThreshold: string;
};

export const defaultFinancialSettings: FinancialSettings = {
  businessName: '',
  taxId: '',
  address: '',
  baseCurrency: 'USD',
  fiscalYearStartMonth: '01',
  fiscalYearStartDay: '01',
  timezone: 'UTC',
  dateFormat: 'YYYY-MM-DD',
  taxDefaultRate: '0',
  taxCustomRules: '',
  taxInclusivePricing: false,
  taxExemptions: '',
  taxBufferPercent: '10',
  linkedAccounts: '',
  paymentMethods: 'stripe,paypal,bank',
  payoutSchedule: 'weekly',
  passTransactionFees: false,
  invoiceLogoUrl: '',
  invoicePrimaryColor: '#CF4500',
  invoiceFont: 'Inter',
  invoicePrefix: 'INV',
  invoiceNumberStart: '1001',
  invoiceDefaultTermsDays: '30',
  invoiceLateFeePolicy: '',
  invoiceAutomatedReminders: true,
  chartOfAccountsCategories: '',
  receiptRules: '',
  ocrEnabled: true,
  mileageRate: '0.67',
  dataExportOptions: 'csv,pdf',
  auditLogsSummary: '',
  approvalWorkflowThreshold: '1000',
};

export function loadFinancialSettings(): FinancialSettings {
  if (typeof localStorage === 'undefined') return { ...defaultFinancialSettings };
  try {
    const raw = getItemMigrated(STORAGE_KEY);
    if (!raw) return { ...defaultFinancialSettings };
    const parsed = JSON.parse(raw) as Partial<FinancialSettings> | null;
    if (!parsed || typeof parsed !== 'object') return { ...defaultFinancialSettings };
    return { ...defaultFinancialSettings, ...parsed };
  } catch {
    return { ...defaultFinancialSettings };
  }
}

export function saveFinancialSettings(value: FinancialSettings): void {
  setItemMigrated(STORAGE_KEY, JSON.stringify(value));
}
