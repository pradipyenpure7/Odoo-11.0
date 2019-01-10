from odoo import api, fields, models, _
import os
import requests
import time
import datetime
import json
from odoo.exceptions import UserError
from random import randrange
from odoo.http import request
import urllib
import base64

class tally_connection(models.Model):
	_name = 'tally.connection'
	_description = 'Tally Connection'
		  

class account_invoice_sendtotally(models.Model):
    _inherit = "account.invoice"
    _description = "account invoice send to tally"

    # create_by | create_date | update_by | update_date
    # Ganesh      30/06/2018    Ganesh      22/10/2018            
    # Info : This function use to send the invoice data in TallyERP9
    @api.multi
    def send_tally(self):   

        account_invoice_data_obj = self.env['account.invoice']
        sale_order_data_obj=self.env['sale.order']
        purchase_order_data_obj=self.env['purchase.order']
        account_invoice_line_obj = self.env['account.invoice.line']
        account_invoice_tax_obj = self.env['account.invoice.tax']
        res_company_obj = self.env['res.company']

        compdata = res_company_obj.search([('id','=',self.env.user.company_id.id)])        
        aidata = account_invoice_data_obj.search([('number','=',self.number)])

        if aidata.partner_id.street2:
            street2 = aidata.partner_id.street2.replace('&','&amp;')
        else:
            street2 = ''    
        print('-------tcustname',aidata.partner_id.tcustname)
        sale_order = sale_order_data_obj.search([('name','=',aidata.origin)])      
        ail_data = account_invoice_line_obj.search([('invoice_id','=',aidata.id)])
        po_data = purchase_order_data_obj.search([('origin','=',sale_order.opf_name)])

        datestr=datetime.datetime.strptime(aidata.date_invoice, "%Y-%m-%d")         #date format come from table and then convert into custome format
        invociedate = datestr.strftime("%d-%b-%Y at %H:%M")
        dateinvoice = datestr.strftime("%Y%m%d")
        #print('---------dsd',invociedate)
        alterid = randrange(0, 100000)
        print('---------alterid',alterid)
        masterid = randrange(0, 100000)
        print('---------masterid',masterid)
        headers = {"Content-type": "text/xml"}
        
        # ItemTaxdtl tag for get tax details from table 
        # It is for child tax calculation
        taxdata=''
        taxdatadtl=''
        itemtaxdtl=''
        self._cr.execute("select at.ttaxname ,round(at.amount,0) as rate,sum(round(((ail.price_subtotal*at.amount)/100),2)) as tax_amt  \
        from account_invoice_line_tax ailt \
        inner join account_invoice_line ail on ail.id=ailt.invoice_line_id \
        inner join account_tax_filiation_rel atfr on atfr.parent_tax = ailt.tax_id and ail.invoice_id=%s \
        inner join account_tax at on at.id=atfr.child_tax where ail.price_subtotal*at.amount>0 and ail.price_subtotal>0 \
        group by at.ttaxname,at.amount order by at.amount",(aidata.id,))
        taxdata = self.env.cr.fetchall()            
        if taxdata:
            taxdatadtl = taxdata
        else:
            # It is for IGST 18 Parent tax calculation
            self._cr.execute("select at.ttaxname,round(at.amount,0) as rate, sum(round(((ail.price_subtotal*at.amount)/100),2)) as tax_amt \
            from account_invoice_line_tax ailt \
            inner join account_invoice_line ail on ail.id=ailt.invoice_line_id and ail.invoice_id = %s \
            inner join account_tax at on at.id=ailt.tax_id where ail.price_subtotal*at.amount>0 and ail.price_subtotal>0 \
            group by at.ttaxname,at.amount order by at.amount",(aidata.id,))
            taxdatadtl = self.env.cr.fetchall()  

        #print('taxdatadtl----',taxdatadtl) 

        for res in taxdatadtl:                
            if int(res[2]) > 0:
                print('in',int(res[2]))
                print('in Query')

                itemtaxdtl+="""<LEDGERENTRIES.LIST>
                <OLDAUDITENTRYIDS.LIST TYPE="Number">
                <OLDAUDITENTRYIDS>-1</OLDAUDITENTRYIDS>
                </OLDAUDITENTRYIDS.LIST>
                <BASICRATEOFINVOICETAX.LIST TYPE="Number">
                <BASICRATEOFINVOICETAX> """+format(res[1])+"""</BASICRATEOFINVOICETAX>
                </BASICRATEOFINVOICETAX.LIST>
                <ROUNDTYPE>Normal Rounding</ROUNDTYPE>
                <LEDGERNAME>"""+format(res[0])+"""</LEDGERNAME>
                <GSTCLASS/>
                <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                <LEDGERFROMITEM>No</LEDGERFROMITEM>
                <REMOVEZEROENTRIES>No</REMOVEZEROENTRIES>
                <ISPARTYLEDGER>No</ISPARTYLEDGER>
                <ISLASTDEEMEDPOSITIVE>No</ISLASTDEEMEDPOSITIVE>
                <ISCAPVATTAXALTERED>No</ISCAPVATTAXALTERED>
                <ISCAPVATNOTCLAIMED>No</ISCAPVATNOTCLAIMED>
                <ROUNDLIMIT> 0</ROUNDLIMIT>
                <AMOUNT>"""+format(res[2])+"""</AMOUNT>
                <VATEXPAMOUNT>"""+format(res[2])+"""</VATEXPAMOUNT>
                <SERVICETAXDETAILS.LIST>       </SERVICETAXDETAILS.LIST>
                <BANKALLOCATIONS.LIST>       </BANKALLOCATIONS.LIST>
                <BILLALLOCATIONS.LIST>       </BILLALLOCATIONS.LIST>
                <INTERESTCOLLECTION.LIST>       </INTERESTCOLLECTION.LIST>
                <OLDAUDITENTRIES.LIST>       </OLDAUDITENTRIES.LIST>
                <ACCOUNTAUDITENTRIES.LIST>       </ACCOUNTAUDITENTRIES.LIST>
                <AUDITENTRIES.LIST>       </AUDITENTRIES.LIST>
                <INPUTCRALLOCS.LIST>       </INPUTCRALLOCS.LIST>
                <DUTYHEADDETAILS.LIST>       </DUTYHEADDETAILS.LIST>
                <EXCISEDUTYHEADDETAILS.LIST>       </EXCISEDUTYHEADDETAILS.LIST>
                <RATEDETAILS.LIST>       </RATEDETAILS.LIST>
                <SUMMARYALLOCS.LIST>       </SUMMARYALLOCS.LIST>
                <STPYMTDETAILS.LIST>       </STPYMTDETAILS.LIST>
                <EXCISEPAYMENTALLOCATIONS.LIST>       </EXCISEPAYMENTALLOCATIONS.LIST>
                <TAXBILLALLOCATIONS.LIST>       </TAXBILLALLOCATIONS.LIST>
                <TAXOBJECTALLOCATIONS.LIST>       </TAXOBJECTALLOCATIONS.LIST>
                <TDSEXPENSEALLOCATIONS.LIST>       </TDSEXPENSEALLOCATIONS.LIST>
                <VATSTATUTORYDETAILS.LIST>       </VATSTATUTORYDETAILS.LIST>
                <COSTTRACKALLOCATIONS.LIST>       </COSTTRACKALLOCATIONS.LIST>
                <REFVOUCHERDETAILS.LIST>       </REFVOUCHERDETAILS.LIST>
                <INVOICEWISEDETAILS.LIST>       </INVOICEWISEDETAILS.LIST>
                <VATITCDETAILS.LIST>       </VATITCDETAILS.LIST>
                <ADVANCETAXDETAILS.LIST>       </ADVANCETAXDETAILS.LIST>
                </LEDGERENTRIES.LIST>
                """	
        # Sales ledger name and basic ammount get from table
        saleledger=''
        salesdata=''
        self._cr.execute("select at.tallyledgername ,sum(ail.price_subtotal) as tax_amt \
        from account_invoice_line_tax ailt \
        inner join account_invoice_line ail on ail.id=ailt.invoice_line_id and ail.invoice_id = %s \
        inner join account_tax at on at.id=ailt.tax_id where ail.price_subtotal>0 \
        group by at.tallyledgername",(aidata.id,))
        salesdata = self.env.cr.fetchall()

        if salesdata:
            for data in salesdata:
                saleledger+="""<LEDGERENTRIES.LIST>
                <OLDAUDITENTRYIDS.LIST TYPE="Number">
                <OLDAUDITENTRYIDS>-1</OLDAUDITENTRYIDS>
                </OLDAUDITENTRYIDS.LIST>
                <LEDGERNAME>"""+data[0]+"""</LEDGERNAME>
                <GSTCLASS/>
                <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                <LEDGERFROMITEM>No</LEDGERFROMITEM>
                <REMOVEZEROENTRIES>No</REMOVEZEROENTRIES>
                <ISPARTYLEDGER>No</ISPARTYLEDGER>
                <ISLASTDEEMEDPOSITIVE>No</ISLASTDEEMEDPOSITIVE>
                <ISCAPVATTAXALTERED>No</ISCAPVATTAXALTERED>
                <AMOUNT>"""+format(data[1])+"""</AMOUNT>
                <SERVICETAXDETAILS.LIST>       </SERVICETAXDETAILS.LIST>
                <BANKALLOCATIONS.LIST>       </BANKALLOCATIONS.LIST>
                <BILLALLOCATIONS.LIST>       </BILLALLOCATIONS.LIST>
                <INTERESTCOLLECTION.LIST>       </INTERESTCOLLECTION.LIST>
                <OLDAUDITENTRIES.LIST>       </OLDAUDITENTRIES.LIST>
                <ACCOUNTAUDITENTRIES.LIST>       </ACCOUNTAUDITENTRIES.LIST>
                <AUDITENTRIES.LIST>       </AUDITENTRIES.LIST>
                <INPUTCRALLOCS.LIST>       </INPUTCRALLOCS.LIST>
                <DUTYHEADDETAILS.LIST>       </DUTYHEADDETAILS.LIST>
                <EXCISEDUTYHEADDETAILS.LIST>       </EXCISEDUTYHEADDETAILS.LIST>
                <RATEDETAILS.LIST>       </RATEDETAILS.LIST>
                <SUMMARYALLOCS.LIST>       </SUMMARYALLOCS.LIST>
                <STPYMTDETAILS.LIST>       </STPYMTDETAILS.LIST>
                <EXCISEPAYMENTALLOCATIONS.LIST>       </EXCISEPAYMENTALLOCATIONS.LIST>
                <TAXBILLALLOCATIONS.LIST>       </TAXBILLALLOCATIONS.LIST>
                <TAXOBJECTALLOCATIONS.LIST>       </TAXOBJECTALLOCATIONS.LIST>
                <TDSEXPENSEALLOCATIONS.LIST>       </TDSEXPENSEALLOCATIONS.LIST>
                <VATSTATUTORYDETAILS.LIST>       </VATSTATUTORYDETAILS.LIST>
                <COSTTRACKALLOCATIONS.LIST>       </COSTTRACKALLOCATIONS.LIST>
                <REFVOUCHERDETAILS.LIST>       </REFVOUCHERDETAILS.LIST>
                <INVOICEWISEDETAILS.LIST>       </INVOICEWISEDETAILS.LIST>
                <VATITCDETAILS.LIST>       </VATITCDETAILS.LIST>
                <ADVANCETAXDETAILS.LIST>       </ADVANCETAXDETAILS.LIST>
                </LEDGERENTRIES.LIST>"""  
        
        #print('saleledger',saleledger)
        # Itemhdrdata tag is header tag with  taxdatadtl and pass item under "GST Net Sale" LEDGER name tag

        itemhdrdata=''
        if aidata.partner_id.tcustname:           
            
            itemhdrdata="""<ENVELOPE>
                <HEADER>
                <TALLYREQUEST>Import Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                <IMPORTDATA>
                <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
                <STATICVARIABLES>
                <SVCURRENTCOMPANY>"""+format(compdata.tcname)+"""</SVCURRENTCOMPANY>
                </STATICVARIABLES>
                </REQUESTDESC>
                <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER REMOTEID="1-"""+format(aidata.number)+"""" VCHKEY="" VCHTYPE="Sales" ACTION="Create" OBJVIEW="Invoice Voucher View">
                <ADDRESS.LIST TYPE="String">
                <ADDRESS>"""+format(aidata.partner_id.street.replace('&','&amp;'))+"""</ADDRESS>
                <ADDRESS>"""+format(street2)+"""</ADDRESS>
                <ADDRESS>"""+format(aidata.partner_id.state_id.name)+"""</ADDRESS>
                <ADDRESS>"""+format(aidata.partner_id.state_id.name)+"""-"""+format(aidata.partner_id.zip)+""", """+format(aidata.partner_id.country_id.name)+"""</ADDRESS>
                </ADDRESS.LIST>
                <BASICBUYERADDRESS.LIST TYPE="String">
                <BASICBUYERADDRESS>"""+format(aidata.partner_id.street.replace('&','&amp;'))+"""</BASICBUYERADDRESS>
                <BASICBUYERADDRESS>"""+format(street2)+"""</BASICBUYERADDRESS>
                <BASICBUYERADDRESS>"""+format(aidata.partner_id.state_id.name)+"""</BASICBUYERADDRESS>
                <BASICBUYERADDRESS>"""+format(aidata.partner_id.state_id.name)+"""-"""+format(aidata.partner_id.zip)+""", """+format(aidata.partner_id.country_id.name)+"""</BASICBUYERADDRESS>
                </BASICBUYERADDRESS.LIST>
                <OLDAUDITENTRYIDS.LIST TYPE="Number">
                <OLDAUDITENTRYIDS>-1</OLDAUDITENTRYIDS>
                </OLDAUDITENTRYIDS.LIST>
                <DATE>"""+format(dateinvoice)+"""</DATE>
                <GUID>1-"""+format(aidata.number)+"""</GUID>
                <STATENAME>"""+format(aidata.partner_id.state_id.name)+"""</STATENAME>
                <GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>
                <VATDEALERTYPE>Regular</VATDEALERTYPE>
                <COUNTRYOFRESIDENCE>"""+format(aidata.partner_id.country_id.name)+"""</COUNTRYOFRESIDENCE>
                <PARTYGSTIN>"""+format(aidata.partner_id.vat)+"""</PARTYGSTIN>
                <PARTYNAME>"""+format(aidata.partner_id.tcustname.replace('&','&amp;'))+"""</PARTYNAME>
                <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                <REFERENCE>"""+format(sale_order.opf_name)+"""</REFERENCE>
                <VOUCHERNUMBER>"""+format(aidata.number)+"""</VOUCHERNUMBER>
                <PARTYLEDGERNAME>"""+format(aidata.partner_id.tcustname.replace('&','&amp;'))+"""</PARTYLEDGERNAME>
                <BASICBASEPARTYNAME>"""+format(aidata.partner_id.tcustname.replace('&','&amp;'))+"""</BASICBASEPARTYNAME>
                <CSTFORMISSUETYPE/>
                <CSTFORMRECVTYPE/>
                <CONSIGNEECSTNUMBER> </CONSIGNEECSTNUMBER>
                <BUYERSCSTNUMBER> </BUYERSCSTNUMBER>
                <FBTPAYMENTTYPE>Default</FBTPAYMENTTYPE>
                <PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>
                <PLACEOFSUPPLY>"""+format(sale_order.partner_shipping_id.state_id.name)+"""</PLACEOFSUPPLY>
                <CONSIGNEEGSTIN>"""+format(aidata.partner_id.vat)+"""</CONSIGNEEGSTIN>
                <BASICBUYERNAME>"""+format(aidata.partner_id.tcustname.replace('&','&amp;'))+"""</BASICBUYERNAME>
                <BASICDUEDATEOFPYMT>"""+format(sale_order.payment_term_id.name.replace('&','&amp;'))+"""</BASICDUEDATEOFPYMT>
                <BASICDATETIMEOFINVOICE>"""+format(invociedate)+"""</BASICDATETIMEOFINVOICE>
                <BASICDATETIMEOFREMOVAL>"""+format(invociedate)+"""</BASICDATETIMEOFREMOVAL>
                <VCHGSTCLASS/>
                <CONSIGNEESTATENAME>"""+format(aidata.partner_id.state_id.name)+"""</CONSIGNEESTATENAME>
                <ENTEREDBY>admin</ENTEREDBY>
                <DIFFACTUALQTY>No</DIFFACTUALQTY>
                <ISMSTFROMSYNC>No</ISMSTFROMSYNC>
                <ASORIGINAL>No</ASORIGINAL>
                <AUDITED>No</AUDITED>
                <FORJOBCOSTING>No</FORJOBCOSTING>
                <ISOPTIONAL>No</ISOPTIONAL>
                <EFFECTIVEDATE>"""+format(dateinvoice)+"""</EFFECTIVEDATE>
                <USEFOREXCISE>No</USEFOREXCISE>
                <ISFORJOBWORKIN>No</ISFORJOBWORKIN>
                <ALLOWCONSUMPTION>No</ALLOWCONSUMPTION>
                <USEFORINTEREST>No</USEFORINTEREST>
                <USEFORGAINLOSS>No</USEFORGAINLOSS>
                <USEFORGODOWNTRANSFER>No</USEFORGODOWNTRANSFER>
                <USEFORCOMPOUND>No</USEFORCOMPOUND>
                <USEFORSERVICETAX>No</USEFORSERVICETAX>
                <ISEXCISEVOUCHER>No</ISEXCISEVOUCHER>
                <EXCISETAXOVERRIDE>No</EXCISETAXOVERRIDE>
                <USEFORTAXUNITTRANSFER>No</USEFORTAXUNITTRANSFER>
                <EXCISEOPENING>No</EXCISEOPENING>
                <USEFORFINALPRODUCTION>No</USEFORFINALPRODUCTION>
                <ISTDSOVERRIDDEN>No</ISTDSOVERRIDDEN>
                <ISTCSOVERRIDDEN>No</ISTCSOVERRIDDEN>
                <ISTDSTCSCASHVCH>No</ISTDSTCSCASHVCH>
                <INCLUDEADVPYMTVCH>No</INCLUDEADVPYMTVCH>
                <ISSUBWORKSCONTRACT>No</ISSUBWORKSCONTRACT>
                <ISVATOVERRIDDEN>No</ISVATOVERRIDDEN>
                <IGNOREORIGVCHDATE>No</IGNOREORIGVCHDATE>
                <ISVATPAIDATCUSTOMS>No</ISVATPAIDATCUSTOMS>
                <ISDECLAREDTOCUSTOMS>No</ISDECLAREDTOCUSTOMS>
                <ISSERVICETAXOVERRIDDEN>No</ISSERVICETAXOVERRIDDEN>
                <ISISDVOUCHER>No</ISISDVOUCHER>
                <ISEXCISEOVERRIDDEN>No</ISEXCISEOVERRIDDEN>
                <ISEXCISESUPPLYVCH>No</ISEXCISESUPPLYVCH>
                <ISGSTOVERRIDDEN>No</ISGSTOVERRIDDEN>
                <GSTNOTEXPORTED>No</GSTNOTEXPORTED>
                <ISVATPRINCIPALACCOUNT>No</ISVATPRINCIPALACCOUNT>
                <ISBOENOTAPPLICABLE>No</ISBOENOTAPPLICABLE>
                <ISSHIPPINGWITHINSTATE>No</ISSHIPPINGWITHINSTATE>
                <ISOVERSEASTOURISTTRANS>No</ISOVERSEASTOURISTTRANS>
                <ISDESIGNATEDZONEPARTY>No</ISDESIGNATEDZONEPARTY>
                <ISCANCELLED>No</ISCANCELLED>
                <HASCASHFLOW>No</HASCASHFLOW>
                <ISPOSTDATED>No</ISPOSTDATED>
                <USETRACKINGNUMBER>No</USETRACKINGNUMBER>
                <ISINVOICE>Yes</ISINVOICE>
                <MFGJOURNAL>No</MFGJOURNAL>
                <HASDISCOUNTS>No</HASDISCOUNTS>
                <ASPAYSLIP>No</ASPAYSLIP>
                <ISCOSTCENTRE>No</ISCOSTCENTRE>
                <ISSTXNONREALIZEDVCH>No</ISSTXNONREALIZEDVCH>
                <ISEXCISEMANUFACTURERON>No</ISEXCISEMANUFACTURERON>
                <ISBLANKCHEQUE>No</ISBLANKCHEQUE>
                <ISVOID>No</ISVOID>
                <ISONHOLD>No</ISONHOLD>
                <ORDERLINESTATUS>No</ORDERLINESTATUS>
                <VATISAGNSTCANCSALES>No</VATISAGNSTCANCSALES>
                <VATISPURCEXEMPTED>No</VATISPURCEXEMPTED>
                <ISVATRESTAXINVOICE>No</ISVATRESTAXINVOICE>
                <VATISASSESABLECALCVCH>No</VATISASSESABLECALCVCH>
                <ISVATDUTYPAID>Yes</ISVATDUTYPAID>
                <ISDELIVERYSAMEASCONSIGNEE>No</ISDELIVERYSAMEASCONSIGNEE>
                <ISDISPATCHSAMEASCONSIGNOR>No</ISDISPATCHSAMEASCONSIGNOR>
                <ISDELETED>No</ISDELETED>
                <CHANGEVCHMODE>No</CHANGEVCHMODE>
                <ALTERID> """+format(alterid)+"""</ALTERID>
                <MASTERID> """+format(masterid)+"""</MASTERID>
                <VOUCHERKEY></VOUCHERKEY>
                <EXCLUDEDTAXATIONS.LIST>      </EXCLUDEDTAXATIONS.LIST>
                <OLDAUDITENTRIES.LIST>      </OLDAUDITENTRIES.LIST>
                <ACCOUNTAUDITENTRIES.LIST>      </ACCOUNTAUDITENTRIES.LIST>
                <AUDITENTRIES.LIST>      </AUDITENTRIES.LIST>
                <DUTYHEADDETAILS.LIST>      </DUTYHEADDETAILS.LIST>
                <SUPPLEMENTARYDUTYHEADDETAILS.LIST>      </SUPPLEMENTARYDUTYHEADDETAILS.LIST>
                <EWAYBILLDETAILS.LIST>      </EWAYBILLDETAILS.LIST>
                <INVOICEDELNOTES.LIST>
                <BASICSHIPPINGDATE>"""+format(dateinvoice)+"""</BASICSHIPPINGDATE>
                <BASICSHIPDELIVERYNOTE>"""+format(aidata.number)+"""</BASICSHIPDELIVERYNOTE>
                </INVOICEDELNOTES.LIST>
                <INVOICEORDERLIST.LIST>
                <BASICORDERDATE>"""+format(dateinvoice)+"""</BASICORDERDATE>
                <BASICPURCHASEORDERNO>"""+format(aidata.name.replace('&','&amp;'))+"""</BASICPURCHASEORDERNO>
                </INVOICEORDERLIST.LIST>
                <INVOICEINDENTLIST.LIST>      </INVOICEINDENTLIST.LIST>
                <ATTENDANCEENTRIES.LIST>      </ATTENDANCEENTRIES.LIST>
                <ORIGINVOICEDETAILS.LIST>      </ORIGINVOICEDETAILS.LIST>
                <INVOICEEXPORTLIST.LIST>      </INVOICEEXPORTLIST.LIST>
                <LEDGERENTRIES.LIST>
                <OLDAUDITENTRYIDS.LIST TYPE="Number">
                <OLDAUDITENTRYIDS>-1</OLDAUDITENTRYIDS>
                </OLDAUDITENTRYIDS.LIST>
                <LEDGERNAME>"""+format(aidata.partner_id.tcustname.replace('&','&amp;'))+"""</LEDGERNAME>
                <GSTCLASS/>
                <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                <LEDGERFROMITEM>No</LEDGERFROMITEM>
                <REMOVEZEROENTRIES>No</REMOVEZEROENTRIES>
                <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
                <ISLASTDEEMEDPOSITIVE>Yes</ISLASTDEEMEDPOSITIVE>
                <ISCAPVATTAXALTERED>No</ISCAPVATTAXALTERED>
                <ISCAPVATNOTCLAIMED>No</ISCAPVATNOTCLAIMED>
                <AMOUNT>-"""+format(aidata.amount_total)+"""</AMOUNT>
                <SERVICETAXDETAILS.LIST></SERVICETAXDETAILS.LIST>
                <BANKALLOCATIONS.LIST></BANKALLOCATIONS.LIST>
                <BILLALLOCATIONS.LIST>
                <NAME>"""+format(aidata.number)+"""</NAME>
                <BILLTYPE>New Ref</BILLTYPE>
                <TDSDEDUCTEEISSPECIALRATE>No</TDSDEDUCTEEISSPECIALRATE>
                <AMOUNT>-"""+format(aidata.amount_total)+"""</AMOUNT>
                <INTERESTCOLLECTION.LIST></INTERESTCOLLECTION.LIST>
                <STBILLCATEGORIES.LIST>        </STBILLCATEGORIES.LIST>
                </BILLALLOCATIONS.LIST>
                <INTERESTCOLLECTION.LIST></INTERESTCOLLECTION.LIST>
                <OLDAUDITENTRIES.LIST></OLDAUDITENTRIES.LIST>
                <ACCOUNTAUDITENTRIES.LIST></ACCOUNTAUDITENTRIES.LIST>
                <AUDITENTRIES.LIST>       </AUDITENTRIES.LIST>
                <INPUTCRALLOCS.LIST>       </INPUTCRALLOCS.LIST>
                <DUTYHEADDETAILS.LIST>       </DUTYHEADDETAILS.LIST>
                <EXCISEDUTYHEADDETAILS.LIST>       </EXCISEDUTYHEADDETAILS.LIST>
                <RATEDETAILS.LIST>       </RATEDETAILS.LIST>
                <SUMMARYALLOCS.LIST>       </SUMMARYALLOCS.LIST>
                <STPYMTDETAILS.LIST>       </STPYMTDETAILS.LIST>
                <EXCISEPAYMENTALLOCATIONS.LIST>       </EXCISEPAYMENTALLOCATIONS.LIST>
                <TAXBILLALLOCATIONS.LIST>       </TAXBILLALLOCATIONS.LIST>
                <TAXOBJECTALLOCATIONS.LIST>       </TAXOBJECTALLOCATIONS.LIST>
                <TDSEXPENSEALLOCATIONS.LIST>       </TDSEXPENSEALLOCATIONS.LIST>
                <VATSTATUTORYDETAILS.LIST>       </VATSTATUTORYDETAILS.LIST>
                <COSTTRACKALLOCATIONS.LIST>       </COSTTRACKALLOCATIONS.LIST>
                <REFVOUCHERDETAILS.LIST>       </REFVOUCHERDETAILS.LIST>
                <INVOICEWISEDETAILS.LIST>       </INVOICEWISEDETAILS.LIST>
                <VATITCDETAILS.LIST>       </VATITCDETAILS.LIST>
                <ADVANCETAXDETAILS.LIST>       </ADVANCETAXDETAILS.LIST>
                </LEDGERENTRIES.LIST>
                """+saleledger+""""""+itemtaxdtl+"""<PAYROLLMODEOFPAYMENT.LIST>
                </PAYROLLMODEOFPAYMENT.LIST>
                <ATTDRECORDS.LIST>      </ATTDRECORDS.LIST>
                <GSTEWAYCONSIGNORADDRESS.LIST>      </GSTEWAYCONSIGNORADDRESS.LIST>
                <GSTEWAYCONSIGNEEADDRESS.LIST>      </GSTEWAYCONSIGNEEADDRESS.LIST>
                <TEMPGSTRATEDETAILS.LIST>      </TEMPGSTRATEDETAILS.LIST>
                </VOUCHER>
                </TALLYMESSAGE>
                <TALLYMESSAGE xmlns:UDF="TallyUDF"><COMPANY>
                <REMOTECMPINFO.LIST MERGE="Yes">
                <NAME>33924d0e-62d5-4228-bc76-595e6a82a9c2</NAME>
                <REMOTECMPNAME>"""+format(compdata.tcname)+"""</REMOTECMPNAME>
                <REMOTECMPSTATE>"""+format(aidata.company_id.state_id.name)+"""</REMOTECMPSTATE>
                </REMOTECMPINFO.LIST>
                </COMPANY>
                </TALLYMESSAGE>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                <COMPANY><REMOTECMPINFO.LIST MERGE="Yes">
                <NAME>33924d0e-62d5-4228-bc76-595e6a82a9c2</NAME>
                <REMOTECMPNAME>"""+format(compdata.tcname)+"""</REMOTECMPNAME>
                <REMOTECMPSTATE>"""+format(aidata.company_id.state_id.name)+"""</REMOTECMPSTATE>
                </REMOTECMPINFO.LIST>
                </COMPANY>
                </TALLYMESSAGE>
                </REQUESTDATA>
                </IMPORTDATA>
                </BODY>
                </ENVELOPE>"""
            #print('---data---',itemhdrdata)
            # Update : Create XML File for Import Invoice entry in tally

            full_path = os.path.realpath(__file__)
            path, filename = os.path.split(full_path)
            print(full_path)
            print(path, filename)
            save_path=path.replace('wizard','download/')
            file_name=''
            if len(itemhdrdata)>1:
                file_name=format(aidata.number.replace('/',''))
                file_name=format(file_name.replace(' ','')+'.xml')
                
            print('###################',file_name)
            outfile = open(save_path+file_name, 'w')
            outfile.write(itemhdrdata)             
            outfile.close()                                 
            result_file = open(save_path+file_name,'rb').read()   
            self._cr.execute("select id from tally_xml_report  where name=%s",(file_name,))
            fileexist = self.env.cr.fetchall()                   
            if fileexist:
                datet = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                self._cr.execute("update tally_xml_report set report=%s ,write_date=%s, downloadid=downloadid+1  where name=%s",(base64.encodestring(result_file),datet,file_name,))
                attach_id = fileexist[0][0]                  
            else:
                ids = self.env['tally.xml.report'].create({
                                            'name':file_name,
                                            'report':base64.encodestring(result_file)
                        })
                attach_id = ids.id                
            return {
                'name': 'Tally XML Download',
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tally.xml.report',
                'res_id':attach_id,
                'data': None,
                'type': 'ir.actions.act_window',
                'target':'new'
            }
        else:
            raise UserError(_("Please fill tally customer name in customer master")) 

# Create class for saving download file in table 23/10/2018
class WizardXMLReport(models.TransientModel):
    _name = "tally.xml.report"
    
    report = fields.Binary('Prepared file',filters='.xml', readonly=True)
    name = fields.Char('File Name', size=32) 
    downloadid = fields.Integer('download count', default=1)  


