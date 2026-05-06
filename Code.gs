// ═══════════════════════════════════════════════════════════════════
//  Gift Aid Declaration Handler
//  Our Lady & St James, Bangor / St David & St Helen, Caernarfon
//  Diocese of Wrexham
//
//  Deploy as a Google Apps Script Web App:
//    Execute as:  Me (p.johnthomas@gmail.com)
//    Who can access: Anyone
//
//  Paste the resulting /exec URL into giftaid.html as GAS_URL.
// ═══════════════════════════════════════════════════════════════════

var PARISH_EMAIL = 'priestbangor@rcdwxm.org.uk';
var FROM_NAME    = 'Gift Aid Form – Our Lady & St James, Bangor';

// ── Entry point ─────────────────────────────────────────────────────
function doPost(e) {
  try {
    var data = JSON.parse(e.parameter.payload);

    sendParishEmail(data);

    if (data.send_copy && data.copy_email) {
      sendDonorEmail(data);
    }

    return jsonResponse({ status: 'ok' });

  } catch (err) {
    Logger.log('Error: ' + err.toString());
    return jsonResponse({ status: 'error', message: err.toString() });
  }
}

// ── Parish email ─────────────────────────────────────────────────────
function sendParishEmail(data) {
  var pdfBlob = buildPdfBlob(data);

  var addrLines = [
    data.address_line1,
    data.address_line2,
    data.town,
    data.county,
    data.postcode
  ].filter(function(l) { return l && l.trim() !== ''; });

  var body = [
    'A Gift Aid declaration has been submitted via the parish website.',
    '',
    '──────────────────────────────────────',
    'DONOR DETAILS',
    '──────────────────────────────────────',
    'Name:           ' + data.full_name,
    'Address:        ' + addrLines.join(', '),
    'Email:          ' + (data.donor_email || 'Not provided'),
    'Tel:            ' + (data.donor_tel   || 'Not provided'),
    '',
    '──────────────────────────────────────',
    'DECLARATION',
    '──────────────────────────────────────',
    'Donation:       £' + data.amount,
    'Purpose:        Upgrade of Sound System, Our Lady & St James, LL57 2EE, Bangor',
    'Charity:        Wrexham Diocesan Trust – Registered Charity No. 700426',
    'Date:           ' + data.date,
    '',
    'The donor has confirmed they are a UK taxpayer and accept Gift Aid',
    'responsibility as required by HMRC.',
    '',
    'The signed declaration PDF is attached to this email.',
    '',
    '──────────────────────────────────────',
    'Parish contact: priestbangor@rcdwxm.org.uk  ·  01248 370421',
    'Submitted via:  ourladysbangor.org',
  ].join('\n');

  GmailApp.sendEmail(
    PARISH_EMAIL,
    'Gift Aid Declaration – ' + data.full_name + ' – ' + data.date,
    body,
    {
      name:        FROM_NAME,
      attachments: [pdfBlob],
    }
  );
}

// ── Donor confirmation email ──────────────────────────────────────────
function sendDonorEmail(data) {
  var pdfBlob = buildPdfBlob(data);

  var body = [
    'Dear ' + data.full_name + ',',
    '',
    'Thank you for your generous donation of £' + data.amount + ' to the',
    'Sound System Appeal at Our Lady & St James, Bangor.',
    '',
    'Your Gift Aid declaration has been received by the parish. A copy',
    'of the signed declaration PDF is attached to this email — please',
    'keep it for your records in case HMRC ever asks you to confirm',
    'your Gift Aid giving.',
    '',
    'Donation details',
    '----------------',
    'Amount:   £' + data.amount,
    'Purpose:  Upgrade of Sound System, Our Lady & St James, Bangor',
    'Date:     ' + data.date,
    '',
    'If you wish to cancel this declaration at any time, or if your',
    'name, home address, or tax status changes, please contact us:',
    '',
    '  Email:  priestbangor@rcdwxm.org.uk',
    '  Tel:    01248 370421',
    '',
    'God bless you,',
    '',
    'Our Lady & St James Parish, Bangor',
    'St David & St Helen, Caernarfon',
    'Diocese of Wrexham',
    'ourladysbangor.org',
  ].join('\n');

  GmailApp.sendEmail(
    data.copy_email,
    'Your Gift Aid Declaration – Our Lady & St James, Bangor',
    body,
    {
      name:        'Our Lady & St James, Bangor',
      attachments: [pdfBlob],
    }
  );
}

// ── Build PDF blob from base64 ────────────────────────────────────────
function buildPdfBlob(data) {
  var bytes = Utilities.base64Decode(data.pdf_base64);
  return Utilities.newBlob(bytes, 'application/pdf', data.pdf_filename);
}

// ── JSON response helper ──────────────────────────────────────────────
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── Optional: test function you can run from the GAS editor ──────────
function testSendToMyself() {
  var testData = {
    full_name:     'Test Donor',
    title:         'Mr',
    first_name:    'Test',
    surname:       'Donor',
    address_line1: '1 Test Street',
    address_line2: '',
    town:          'Bangor',
    county:        'Gwynedd',
    postcode:      'LL57 1AA',
    date:          'May 2026',
    donor_email:   'p.johnthomas@gmail.com',
    donor_tel:     '',
    amount:        '25.00',
    send_copy:     true,
    copy_email:    'p.johnthomas@gmail.com',
    pdf_base64:    '',   // empty — GAS will make a zero-byte blob; fine for routing test
    pdf_filename:  'GiftAid_Test_May_2026.pdf',
  };
  sendParishEmail(testData);
  Logger.log('Test email sent to ' + PARISH_EMAIL);
}
