import type { InvoiceExportConfig } from '../types/invoiceExport';
import { createLineItem, defaultInvoiceDocument, defaultParty, type PartyDetails } from '../types/invoiceDocument';

export type InvoiceTemplateId =
  | 'blank'
  | 'consulting_hours'
  | 'product_sale'
  | 'retainer'
  | 'services_fixed';

export const INVOICE_TEMPLATES: { id: InvoiceTemplateId; label: string; hint: string }[] = [
  { id: 'blank', label: 'Blank', hint: 'Reset document fields' },
  { id: 'consulting_hours', label: 'Consulting', hint: 'Hourly + expense pass-through' },
  { id: 'product_sale', label: 'Product sale', hint: 'SKU items + shipping line' },
  { id: 'retainer', label: 'Monthly retainer', hint: 'Monthly fee + SLA support' },
  { id: 'services_fixed', label: 'Project', hint: 'Milestones + handover payment' },
];

function keepOrFallbackParty(party: PartyDetails, fallbackName: string): PartyDetails {
  const hasAnyValue = Object.values(party).some((v) => String(v ?? '').trim().length > 0);
  if (hasAnyValue) return { ...party };
  return {
    ...defaultParty(),
    legalName: fallbackName,
  };
}

/** Partial patch to merge into current export config (keeps logo, fonts, format unless overridden). */
export function applyInvoiceTemplate(
  id: InvoiceTemplateId,
  current: InvoiceExportConfig
): Partial<InvoiceExportConfig> {
  const baseDoc = current.document;
  const today = new Date();
  const due = new Date(today);
  due.setDate(due.getDate() + 30);
  const dates = {
    issueDate: today.toISOString().slice(0, 10),
    dueDate: due.toISOString().slice(0, 10),
  };

  switch (id) {
    case 'blank':
      return {
        document: defaultInvoiceDocument(),
      };

    case 'consulting_hours':
      return {
        fontFamily: 'Helvetica',
        fontSize: 12,
        primaryColor: '#141413',
        secondaryColor: '#CF4500',
        outputFormat: 'pdf',
        document: {
          ...baseDoc,
          ...dates,
          invoiceNumber: baseDoc.invoiceNumber.trim() || 'CONS-YYYY-001',
          lineItems: [
            createLineItem({
              description: 'Professional consulting services',
              quantity: 16,
              unitLabel: 'hours',
              unitPrice: 180,
            }),
            createLineItem({
              description: 'Research and preparation',
              quantity: 4,
              unitLabel: 'hours',
              unitPrice: 180,
            }),
            createLineItem({
              description: 'Expense pass-through (tools / APIs)',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 120,
            }),
          ],
          notes:
            'Billing basis: hourly consulting and approved pass-through costs.\nPayment terms: net 14 days.\nLate fees may apply after due date where permitted.',
          supplier: keepOrFallbackParty(baseDoc.supplier, 'Consulting Studio LLC'),
          customer: keepOrFallbackParty(baseDoc.customer, 'Client Company Ltd'),
        },
      };

    case 'product_sale':
      return {
        fontFamily: 'Courier',
        fontSize: 11,
        primaryColor: '#1F3A5F',
        secondaryColor: '#2E7D32',
        outputFormat: 'xlsx',
        document: {
          ...baseDoc,
          ...dates,
          invoiceNumber: baseDoc.invoiceNumber.trim() || 'SKU-YYYY-001',
          lineItems: [
            createLineItem({
              description: 'SKU-A100 · Core hardware unit',
              quantity: 3,
              unitLabel: 'units',
              unitPrice: 249,
            }),
            createLineItem({
              description: 'SKU-B220 · Extended accessory pack',
              quantity: 3,
              unitLabel: 'units',
              unitPrice: 59,
            }),
            createLineItem({
              description: 'Shipping & handling',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 85,
            }),
          ],  
          notes:
            'Goods sold per itemized SKUs above.\nTaxes, duties, and customs are excluded unless explicitly listed.\nRisk transfers on dispatch unless agreed otherwise.',
          supplier: keepOrFallbackParty(baseDoc.supplier, 'Distribution Co.'),
          customer: keepOrFallbackParty(baseDoc.customer, 'Buying Entity'),
        },
      };

    case 'retainer':
      return {
        fontFamily: 'Times-Roman',
        fontSize: 12,
        primaryColor: '#17324D',
        secondaryColor: '#0F6B4F',
        outputFormat: 'pdf',
        document: {
          ...baseDoc,
          ...dates,
          invoiceNumber: baseDoc.invoiceNumber.trim() || 'RET-YYYY-MM',
          lineItems: [
            createLineItem({
              description: 'Monthly retainer — ongoing advisory & support',
              quantity: 1,
              unitLabel: 'days',
              unitPrice: 3500,
            }),
            createLineItem({
              description: 'On-call priority support (SLA)',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 500,
            }),
          ],
          notes:
            'Retainer covers the billing period shown on this invoice.\nIncludes advisory sessions, planning, and agreed SLA response windows.\nAdditional out-of-scope work is billed separately.',
          supplier: keepOrFallbackParty(baseDoc.supplier, 'Advisory Partner LLC'),
          customer: keepOrFallbackParty(baseDoc.customer, 'Retainer Client'),
        },
      };

    case 'services_fixed':
      return {
        fontFamily: 'Helvetica',
        fontSize: 12,
        primaryColor: '#4A1D96',
        secondaryColor: '#9333EA',
        outputFormat: 'docx',
        document: {
          ...baseDoc,
          ...dates,
          invoiceNumber: baseDoc.invoiceNumber.trim() || 'PROJ-YYYY-001',
          lineItems: [
            createLineItem({
              description: 'Project milestone 1 — discovery & architecture',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 6000,
            }),
            createLineItem({
              description: 'Project milestone 2 — implementation',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 10000,
            }),
            createLineItem({
              description: 'Final acceptance & handover',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 4000,
            }),
          ],
          notes:
            'Milestone billing per statement of work.\nFinal payment due on acceptance and handover.\nSupport window starts on project completion date.',
          supplier: keepOrFallbackParty(baseDoc.supplier, 'Project Delivery Studio'),
          customer: keepOrFallbackParty(baseDoc.customer, 'Project Client'),
        },
      };

    default:
      return {};
  }
}
