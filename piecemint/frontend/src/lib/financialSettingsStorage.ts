import { getItemMigrated, setItemMigrated } from './localStorageScope';

const STORAGE_KEY = 'ff_financial_settings_v1';
export const payoutScheduleOptions = ['daily', 'weekly', 'biweekly', 'monthly', 'manual'] as const;
const payoutScheduleAliasMap: Record<string, (typeof payoutScheduleOptions)[number]> = {
  day: 'daily',
  daily: 'daily',
  week: 'weekly',
  weekly: 'weekly',
  'every week': 'weekly',
  'once a week': 'weekly',
  biweekly: 'biweekly',
  'bi-weekly': 'biweekly',
  fortnightly: 'biweekly',
  'every 2 weeks': 'biweekly',
  monthly: 'monthly',
  month: 'monthly',
  'once a month': 'monthly',
  manual: 'manual',
  on_demand: 'manual',
  ondemand: 'manual',
  ad_hoc: 'manual',
  adhoc: 'manual',
};

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
  paymentMethods: string[];
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
  dataExportOptions: string[];
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
  paymentMethods: ['stripe', 'paypal', 'bank_transfer'],
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
  dataExportOptions: ['csv', 'pdf'],
  auditLogsSummary: '',
  approvalWorkflowThreshold: '1000',
};

export function normalizePayoutSchedule(value: unknown): FinancialSettings['payoutSchedule'] {
  if (typeof value !== 'string') return defaultFinancialSettings.payoutSchedule;
  const normalized = value.trim().toLowerCase().replace(/\s+/g, ' ');
  return payoutScheduleAliasMap[normalized] ?? defaultFinancialSettings.payoutSchedule;
}

export function loadFinancialSettings(): FinancialSettings {
  if (typeof localStorage === 'undefined') return { ...defaultFinancialSettings };
  try {
    const raw = getItemMigrated(STORAGE_KEY);
    if (!raw) return { ...defaultFinancialSettings };
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== 'object') return { ...defaultFinancialSettings };
    const parsedRecord = parsed as Record<string, unknown>;
    const rawExportOptions = parsedRecord.dataExportOptions;
    const rawPaymentMethods = parsedRecord.paymentMethods;
    const rawPayoutSchedule = parsedRecord.payoutSchedule;
    const normalizedExportOptions = Array.isArray(rawExportOptions)
      ? rawExportOptions.filter((value): value is string => typeof value === 'string')
      : typeof rawExportOptions === 'string'
        ? rawExportOptions
            .split(',')
            .map((value) => value.trim().toLowerCase())
            .filter(Boolean)
        : defaultFinancialSettings.dataExportOptions;
    const normalizedPaymentMethods = Array.isArray(rawPaymentMethods)
      ? rawPaymentMethods.filter((value): value is string => typeof value === 'string')
      : typeof rawPaymentMethods === 'string'
        ? rawPaymentMethods
            .split(',')
            .map((value) => value.trim().toLowerCase())
            .filter(Boolean)
            .map((value) => (value === 'bank' ? 'bank_transfer' : value))
        : defaultFinancialSettings.paymentMethods;
    return {
      ...defaultFinancialSettings,
      ...(parsedRecord as Partial<FinancialSettings>),
      dataExportOptions: normalizedExportOptions,
      paymentMethods: normalizedPaymentMethods,
      payoutSchedule: normalizePayoutSchedule(rawPayoutSchedule),
    };
  } catch {
    return { ...defaultFinancialSettings };
  }
}

export function saveFinancialSettings(value: FinancialSettings): void {
  setItemMigrated(STORAGE_KEY, JSON.stringify(value));
}
