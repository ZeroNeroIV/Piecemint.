import { useMemo, useState, type ReactNode } from 'react';
import {
  defaultFinancialSettings,
  loadFinancialSettings,
  payoutScheduleOptions,
  saveFinancialSettings,
  type FinancialSettings,
} from '../lib/financialSettingsStorage';

type StringSettingKey = {
  [K in keyof FinancialSettings]: FinancialSettings[K] extends string ? K : never;
}[keyof FinancialSettings];

type BooleanSettingKey = {
  [K in keyof FinancialSettings]: FinancialSettings[K] extends boolean ? K : never;
}[keyof FinancialSettings];

type FieldProps = {
  id: StringSettingKey;
  label: string;
  value: string;
  onChange: (id: StringSettingKey, value: string) => void;
  placeholder?: string;
  type?: 'text' | 'number' | 'url' | 'color';
};

function TextField({ id, label, value, onChange, placeholder, type = 'text' }: FieldProps) {
  return (
    <label className="flex flex-col gap-2 text-sm font-medium text-ink-black/85" htmlFor={id}>
      {label}
      <input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(id, e.target.value)}
        className="rounded-2xl border border-ink-black/15 bg-white px-4 py-2.5 text-sm outline-none transition-colors focus:border-ink-black/35"
      />
    </label>
  );
}

function TextAreaField({
  id,
  label,
  value,
  onChange,
  placeholder,
}: Omit<FieldProps, 'type'> & { rows?: number }) {
  return (
    <label className="flex flex-col gap-2 text-sm font-medium text-ink-black/85" htmlFor={id}>
      {label}
      <textarea
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(id, e.target.value)}
        rows={3}
        className="rounded-2xl border border-ink-black/15 bg-white px-4 py-2.5 text-sm outline-none transition-colors focus:border-ink-black/35"
      />
    </label>
  );
}

function ToggleField({
  id,
  label,
  checked,
  onChange,
}: {
  id: BooleanSettingKey;
  label: string;
  checked: boolean;
  onChange: (id: BooleanSettingKey, checked: boolean) => void;
}) {
  return (
    <label
      className="flex items-center justify-between gap-4 rounded-2xl border border-ink-black/10 bg-white/75 px-4 py-3"
      htmlFor={id}
    >
      <span className="text-sm font-medium text-ink-black/85">{label}</span>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(id, !checked)}
        className={[
          'relative inline-flex h-7 w-12 items-center rounded-full border transition-colors',
          checked
            ? 'border-signal-orange bg-signal-orange/80'
            : 'border-ink-black/25 bg-ink-black/15',
        ].join(' ')}
      >
        <span
          className={[
            'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
            checked ? 'translate-x-6' : 'translate-x-1',
          ].join(' ')}
        />
      </button>
    </label>
  );
}

function Section({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="card space-y-5">
      <header className="space-y-1">
        <h2 className="text-xl font-medium tracking-tight">{title}</h2>
        <p className="text-sm text-ink-black/65">{description}</p>
      </header>
      {children}
    </section>
  );
}

export default function FinancialSettingsPage() {
  const [settings, setSettings] = useState<FinancialSettings>(() => loadFinancialSettings());
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const onTextChange = (id: StringSettingKey, value: string) => {
    setSettings((prev) => ({ ...prev, [id]: value }));
  };

  const onToggleChange = (id: BooleanSettingKey, checked: boolean) => {
    setSettings((prev) => ({ ...prev, [id]: checked }));
  };

  const onExportOptionToggle = (option: string, checked: boolean) => {
    setSettings((prev) => ({
      ...prev,
      dataExportOptions: checked
        ? [...prev.dataExportOptions, option]
        : prev.dataExportOptions.filter((value) => value !== option),
    }));
  };

  const onPaymentMethodToggle = (method: string, checked: boolean) => {
    setSettings((prev) => ({
      ...prev,
      paymentMethods: checked
        ? [...prev.paymentMethods, method]
        : prev.paymentMethods.filter((value) => value !== method),
    }));
  };

  const onSave = () => {
    saveFinancialSettings(settings);
    setSavedAt(new Date().toLocaleTimeString());
  };

  const onReset = () => {
    setSettings({ ...defaultFinancialSettings });
    saveFinancialSettings({ ...defaultFinancialSettings });
    setSavedAt(new Date().toLocaleTimeString());
  };

  const baseCurrencyOptions = useMemo(
    () => ['USD', 'EUR', 'GBP', 'AED', 'SAR', 'TRY', 'INR'],
    []
  );
  const dataExportOptions = useMemo(
    () => [
      { value: 'csv', label: 'CSV' },
      { value: 'pdf', label: 'PDF' },
      { value: 'qbo', label: 'QBO' },
    ],
    []
  );
  const paymentMethodOptions = useMemo(
    () => [
      { value: 'stripe', label: 'Stripe' },
      { value: 'paypal', label: 'PayPal' },
      { value: 'bank_transfer', label: 'Bank transfer' },
    ],
    []
  );
  const payoutScheduleLabels = useMemo<Record<string, string>>(
    () => ({
      daily: 'Daily',
      weekly: 'Weekly',
      biweekly: 'Biweekly',
      monthly: 'Monthly',
      manual: 'Manual',
    }),
    []
  );

  return (
    <div className="w-full space-y-8">
      <header className="max-w-3xl">
        <h1 className="text-3xl md:text-4xl font-medium tracking-tight mb-2">Financial Settings</h1>
        <p className="text-ink-black/70">
          Configure core finance preferences for localization, tax, billing, expense policy, and compliance.
          Settings are currently stored locally on this device.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="pill-button" onClick={onSave}>
          Save settings
        </button>
        <button type="button" className="pill-button-secondary" onClick={onReset}>
          Reset defaults
        </button>
        {savedAt && <p className="text-sm text-ink-black/60">Last saved at {savedAt}</p>}
      </div>

      <Section
        title="Business Profile & Localization"
        description="Legal identity, region defaults, and fiscal timeline used across reports and invoicing."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField id="businessName" label="Business name" value={settings.businessName} onChange={onTextChange} />
          <TextField id="taxId" label="Tax ID" value={settings.taxId} onChange={onTextChange} />
          <TextAreaField id="address" label="Address" value={settings.address} onChange={onTextChange} />
          <label className="flex flex-col gap-2 text-sm font-medium text-ink-black/85" htmlFor="baseCurrency">
            Base currency
            <select
              id="baseCurrency"
              value={settings.baseCurrency}
              onChange={(e) => onTextChange('baseCurrency', e.target.value)}
              className="rounded-2xl border border-ink-black/15 bg-white px-4 py-2.5 text-sm outline-none transition-colors focus:border-ink-black/35"
            >
              {baseCurrencyOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <TextField
            id="fiscalYearStartMonth"
            label="Fiscal year start month (MM)"
            value={settings.fiscalYearStartMonth}
            onChange={onTextChange}
            placeholder="01"
          />
          <TextField
            id="fiscalYearStartDay"
            label="Fiscal year start day (DD)"
            value={settings.fiscalYearStartDay}
            onChange={onTextChange}
            placeholder="01"
          />
          <TextField id="timezone" label="Timezone" value={settings.timezone} onChange={onTextChange} placeholder="UTC" />
          <TextField
            id="dateFormat"
            label="Date format"
            value={settings.dateFormat}
            onChange={onTextChange}
            placeholder="YYYY-MM-DD"
          />
        </div>
      </Section>

      <Section
        title="Tax Configuration"
        description="Define default/custom tax behavior, inclusivity rules, exemptions, and tax cash reserve strategy."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField
            id="taxDefaultRate"
            label="Default tax rate (%)"
            type="number"
            value={settings.taxDefaultRate}
            onChange={onTextChange}
          />
          <TextField
            id="taxBufferPercent"
            label="Tax Buffer (%) of incoming funds"
            type="number"
            value={settings.taxBufferPercent}
            onChange={onTextChange}
          />
          <TextAreaField
            id="taxCustomRules"
            label="Custom tax rules"
            value={settings.taxCustomRules}
            onChange={onTextChange}
            placeholder="Example: Services=15%, Digital goods=8%"
          />
          <TextAreaField
            id="taxExemptions"
            label="Tax exemptions"
            value={settings.taxExemptions}
            onChange={onTextChange}
            placeholder="Example: Exempt clients, products, jurisdictions"
          />
        </div>
        <ToggleField
          id="taxInclusivePricing"
          label="Tax-inclusive pricing"
          checked={settings.taxInclusivePricing}
          onChange={onToggleChange}
        />
      </Section>

      <Section
        title="Payment & Payout Gateways"
        description="Manage connected gateways, accepted methods, payout cadence, and fee accounting policy."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextAreaField
            id="linkedAccounts"
            label="Linked accounts"
            value={settings.linkedAccounts}
            onChange={onTextChange}
            placeholder="Example: Stripe acct_..., PayPal merchant email, bank alias"
          />
          <fieldset className="flex flex-col gap-2 text-sm font-medium text-ink-black/85">
            <legend className="mb-0.5">Payment methods</legend>
            <div className="rounded-2xl border border-ink-black/15 bg-white p-3">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {paymentMethodOptions.map((option) => (
                  <label
                    key={option.value}
                    htmlFor={`payment-method-option-${option.value}`}
                    className="group relative cursor-pointer"
                  >
                    <input
                      id={`payment-method-option-${option.value}`}
                      type="checkbox"
                      checked={settings.paymentMethods.includes(option.value)}
                      onChange={(e) => onPaymentMethodToggle(option.value, e.target.checked)}
                      className="peer sr-only"
                    />
                    <span className="flex items-center rounded-xl border border-ink-black/15 bg-white px-3 py-2.5 text-sm font-medium text-ink-black/90 transition-all group-hover:border-ink-black/30 peer-focus-visible:ring-2 peer-focus-visible:ring-signal-orange/40 peer-checked:border-signal-orange/70 peer-checked:bg-signal-orange/10">
                      <span>{option.label}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </fieldset>
          <label className="flex flex-col gap-2 text-sm font-medium text-ink-black/85" htmlFor="payoutSchedule">
            Payout schedule
            <select
              id="payoutSchedule"
              value={settings.payoutSchedule}
              onChange={(e) => onTextChange('payoutSchedule', e.target.value)}
              className="rounded-2xl border border-ink-black/15 bg-white px-4 py-2.5 text-sm outline-none transition-colors focus:border-ink-black/35"
            >
              {payoutScheduleOptions.map((value) => (
                <option key={value} value={value}>
                  {payoutScheduleLabels[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <ToggleField
          id="passTransactionFees"
          label="Pass transaction fees to customer pricing"
          checked={settings.passTransactionFees}
          onChange={onToggleChange}
        />
      </Section>

      <Section
        title="Invoicing & Billing Preferences"
        description="Customize invoice look-and-feel, numbering, payment terms, penalties, and reminder behavior."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField id="invoiceLogoUrl" label="Invoice logo URL" type="url" value={settings.invoiceLogoUrl} onChange={onTextChange} />
          <TextField id="invoicePrimaryColor" label="Invoice accent color" type="color" value={settings.invoicePrimaryColor} onChange={onTextChange} />
          <TextField id="invoiceFont" label="Invoice font" value={settings.invoiceFont} onChange={onTextChange} placeholder="Inter" />
          <TextField id="invoicePrefix" label="Invoice prefix" value={settings.invoicePrefix} onChange={onTextChange} placeholder="INV" />
          <TextField
            id="invoiceNumberStart"
            label="Starting invoice number"
            value={settings.invoiceNumberStart}
            onChange={onTextChange}
          />
          <TextField
            id="invoiceDefaultTermsDays"
            label="Default payment terms (days)"
            type="number"
            value={settings.invoiceDefaultTermsDays}
            onChange={onTextChange}
          />
          <TextAreaField
            id="invoiceLateFeePolicy"
            label="Late fee policy"
            value={settings.invoiceLateFeePolicy}
            onChange={onTextChange}
            placeholder="Example: 1.5% monthly after due date"
          />
        </div>
        <ToggleField
          id="invoiceAutomatedReminders"
          label="Automated invoice reminders"
          checked={settings.invoiceAutomatedReminders}
          onChange={onToggleChange}
        />
      </Section>

      <Section
        title="Expense & Category Management"
        description="Set category taxonomy and expense capture rules, including OCR and mileage reimbursements."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextAreaField
            id="chartOfAccountsCategories"
            label="Chart of accounts categories"
            value={settings.chartOfAccountsCategories}
            onChange={onTextChange}
            placeholder="Example: Revenue, COGS, Marketing, Payroll"
          />
          <TextAreaField
            id="receiptRules"
            label="Receipt rules"
            value={settings.receiptRules}
            onChange={onTextChange}
            placeholder="Example: Auto-match receipts under $100"
          />
          <TextField
            id="mileageRate"
            label="Mileage rate"
            type="number"
            value={settings.mileageRate}
            onChange={onTextChange}
            placeholder="0.67"
          />
        </div>
        <ToggleField id="ocrEnabled" label="Receipt OCR enabled" checked={settings.ocrEnabled} onChange={onToggleChange} />
      </Section>

      <Section
        title="Security & Compliance"
        description="Control exports, approval workflow limits, and keep lightweight audit context."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <fieldset className="flex flex-col gap-2 text-sm font-medium text-ink-black/85">
            <legend className="mb-0.5">Data export options</legend>
            <div className="rounded-2xl border border-ink-black/15 bg-white p-3">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {dataExportOptions.map((option) => (
                <label
                  key={option.value}
                  htmlFor={`data-export-option-${option.value}`}
                  className="group relative cursor-pointer"
                >
                  <input
                    id={`data-export-option-${option.value}`}
                    type="checkbox"
                    checked={settings.dataExportOptions.includes(option.value)}
                    onChange={(e) => onExportOptionToggle(option.value, e.target.checked)}
                    className="peer sr-only"
                  />
                  <span className="flex items-center rounded-xl border border-ink-black/15 bg-white px-3 py-2.5 text-sm font-medium text-ink-black/90 transition-all group-hover:border-ink-black/30 peer-focus-visible:ring-2 peer-focus-visible:ring-signal-orange/40 peer-checked:border-signal-orange/70 peer-checked:bg-signal-orange/10">
                    <span>{option.label}</span>
                  </span>
                </label>
              ))}
              </div>
            </div>
          </fieldset>
          <TextField
            id="approvalWorkflowThreshold"
            label="Approval threshold amount"
            type="number"
            value={settings.approvalWorkflowThreshold}
            onChange={onTextChange}
            placeholder="1000"
          />
          <TextAreaField
            id="auditLogsSummary"
            label="Audit logs summary"
            value={settings.auditLogsSummary}
            onChange={onTextChange}
            placeholder="Short notes about access reviews, policy checks, incidents"
          />
        </div>
      </Section>
    </div>
  );
}
