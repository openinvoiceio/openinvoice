import { TaxIdTypeEnum } from "@/api/models";

export const MAX_TAX_IDS = 5;

export const TAX_ID_TYPES = Object.values(TaxIdTypeEnum) as TaxIdTypeEnum[];

export const TAX_ID_NUMBER_HINTS: Record<TaxIdTypeEnum, string> = {
  [TaxIdTypeEnum.unknown]: "123456789",
  [TaxIdTypeEnum.ad_nrt]: "F123456X",
  [TaxIdTypeEnum.ae_trn]: "100123456700003", // 15 digits
  [TaxIdTypeEnum.al_tin]: "J12345678L",
  [TaxIdTypeEnum.am_tin]: "123456789",
  [TaxIdTypeEnum.ao_tin]: "5001234567",
  [TaxIdTypeEnum.ar_cuit]: "20-12345678-3", // 11 digits
  [TaxIdTypeEnum.au_abn]: "12 345 678 901", // 11 digits
  [TaxIdTypeEnum.au_arn]: "123 456 789", // 9 digits
  [TaxIdTypeEnum.aw_tin]: "123456789",
  [TaxIdTypeEnum.az_tin]: "1234567890",
  [TaxIdTypeEnum.ba_tin]: "123456789",
  [TaxIdTypeEnum.bb_tin]: "123456789",
  [TaxIdTypeEnum.bd_bin]: "1234567890",
  [TaxIdTypeEnum.bf_ifu]: "1234567890",
  [TaxIdTypeEnum.bg_uic]: "123456789", // 9/10 digits
  [TaxIdTypeEnum.bh_vat]: "12345678", // 8 digits
  [TaxIdTypeEnum.bj_ifu]: "1234567890123",
  [TaxIdTypeEnum.bo_tin]: "123456789",
  [TaxIdTypeEnum.br_cnpj]: "12.345.678/0001-95", // 14 digits
  [TaxIdTypeEnum.br_cpf]: "123.456.789-09", // 11 digits
  [TaxIdTypeEnum.bs_tin]: "123456789",
  [TaxIdTypeEnum.by_tin]: "123456789",
  [TaxIdTypeEnum.ca_bn]: "123456789", // 9 digits
  [TaxIdTypeEnum.ca_gst_hst]: "123456789RT0001", // BN + RT + branch
  [TaxIdTypeEnum.ca_pst_bc]: "PST-1234-5678",
  [TaxIdTypeEnum.ca_pst_mb]: "1234-5678-901",
  [TaxIdTypeEnum.ca_pst_sk]: "1234-567-8",
  [TaxIdTypeEnum.ca_qst]: "1234567890TQ0001",
  [TaxIdTypeEnum.cd_nif]: "A1234567B",
  [TaxIdTypeEnum.ch_uid]: "CHE-123.456.789",
  [TaxIdTypeEnum.ch_vat]: "CHE-123.456.789 MWST",
  [TaxIdTypeEnum.cl_tin]: "12.345.678-5", // RUT
  [TaxIdTypeEnum.cm_niu]: "M1234567890",
  [TaxIdTypeEnum.cn_tin]: "123456789012345",
  [TaxIdTypeEnum.co_nit]: "123.456.789-0",
  [TaxIdTypeEnum.cr_tin]: "301230456",
  [TaxIdTypeEnum.cv_nif]: "123456789",
  [TaxIdTypeEnum.de_stn]: "12/345/67890",
  [TaxIdTypeEnum.do_rcn]: "123456789",
  [TaxIdTypeEnum.ec_ruc]: "1790012345001", // 13 digits
  [TaxIdTypeEnum.eg_tin]: "123456789",
  [TaxIdTypeEnum.es_cif]: "B12345678",
  [TaxIdTypeEnum.et_tin]: "123456789",
  [TaxIdTypeEnum.eu_oss_vat]: "PL1234567890",
  [TaxIdTypeEnum.eu_vat]: "DE123456789",
  [TaxIdTypeEnum.gb_vat]: "GB123456789", // 9 digits (sometimes 12)
  [TaxIdTypeEnum.ge_vat]: "123456789",
  [TaxIdTypeEnum.gn_nif]: "123456789",
  [TaxIdTypeEnum.hk_br]: "12345678", // 8 digits
  [TaxIdTypeEnum.hr_oib]: "12345678901", // 11 digits
  [TaxIdTypeEnum.hu_tin]: "12345678-1-12",
  [TaxIdTypeEnum.id_npwp]: "12.345.678.9-012.345",
  [TaxIdTypeEnum.il_vat]: "123456782", // 9 digits
  [TaxIdTypeEnum.in_gst]: "27ABCDE1234F1Z5", // 15 chars
  [TaxIdTypeEnum.is_vat]: "123456",
  [TaxIdTypeEnum.jp_cn]: "1234567890123", // 13 digits corporate number
  [TaxIdTypeEnum.jp_rn]: "1234567890123",
  [TaxIdTypeEnum.jp_trn]: "T1234567890123", // TRN
  [TaxIdTypeEnum.ke_pin]: "A123456789B",
  [TaxIdTypeEnum.kg_tin]: "123456789",
  [TaxIdTypeEnum.kh_tin]: "123456789",
  [TaxIdTypeEnum.kr_brn]: "123-45-67890", // 10 digits
  [TaxIdTypeEnum.kz_bin]: "123456789012", // 12 digits
  [TaxIdTypeEnum.la_tin]: "123456789",
  [TaxIdTypeEnum.li_uid]: "FL-123.456.789-0",
  [TaxIdTypeEnum.li_vat]: "LI12345",
  [TaxIdTypeEnum.ma_vat]: "12345678",
  [TaxIdTypeEnum.md_vat]: "1234567890123",
  [TaxIdTypeEnum.me_pib]: "12345678",
  [TaxIdTypeEnum.mk_vat]: "MK1234567890123", // 13 digits
  [TaxIdTypeEnum.mr_nif]: "12345678",
  [TaxIdTypeEnum.mx_rfc]: "ABC010203AB1", // 12/13 chars
  [TaxIdTypeEnum.my_frp]: "1234567890",
  [TaxIdTypeEnum.my_itn]: "1234567890",
  [TaxIdTypeEnum.my_sst]: "A12-3456-7890",
  [TaxIdTypeEnum.ng_tin]: "12345678-0001",
  [TaxIdTypeEnum.no_vat]: "123456789MVA",
  [TaxIdTypeEnum.no_voec]: "VOEC123456",
  [TaxIdTypeEnum.np_pan]: "123456789",
  [TaxIdTypeEnum.nz_gst]: "123-456-789",
  [TaxIdTypeEnum.om_vat]: "1234567890",
  [TaxIdTypeEnum.pe_ruc]: "20123456789", // 11 digits
  [TaxIdTypeEnum.ph_tin]: "123-456-789-000", // 9–12
  [TaxIdTypeEnum.ro_tin]: "RO12345678",
  [TaxIdTypeEnum.rs_pib]: "123456789", // 9 digits
  [TaxIdTypeEnum.ru_inn]: "7701234567", // 10 or 12 digits
  [TaxIdTypeEnum.ru_kpp]: "770101001", // 9 digits
  [TaxIdTypeEnum.sa_vat]: "310123456789003", // 15 digits
  [TaxIdTypeEnum.sg_gst]: "M12345678X",
  [TaxIdTypeEnum.sg_uen]: "201123456A",
  [TaxIdTypeEnum.si_tin]: "SI12345678",
  [TaxIdTypeEnum.sn_ninea]: "123456789",
  [TaxIdTypeEnum.sr_fin]: "123456789",
  [TaxIdTypeEnum.sv_nit]: "0614-290998-102-3",
  [TaxIdTypeEnum.th_vat]: "1234567890123", // 13 digits
  [TaxIdTypeEnum.tj_tin]: "123456789",
  [TaxIdTypeEnum.tr_tin]: "1234567890", // 10 digits
  [TaxIdTypeEnum.tw_vat]: "12345678", // 8 digits
  [TaxIdTypeEnum.tz_vat]: "123-456-789",
  [TaxIdTypeEnum.ua_vat]: "123456789012", // 12 digits
  [TaxIdTypeEnum.ug_tin]: "1001234567",
  [TaxIdTypeEnum.us_ein]: "12-3456789",
  [TaxIdTypeEnum.uy_ruc]: "123456780019", // 12 digits
  [TaxIdTypeEnum.uz_tin]: "123456789",
  [TaxIdTypeEnum.uz_vat]: "123456789",
  [TaxIdTypeEnum.ve_rif]: "J-12345678-9",
  [TaxIdTypeEnum.vn_tin]: "0101234567",
  [TaxIdTypeEnum.za_vat]: "4123456789", // 10 digits
  [TaxIdTypeEnum.zm_tin]: "1001234567",
  [TaxIdTypeEnum.zw_tin]: "123456789",
};
