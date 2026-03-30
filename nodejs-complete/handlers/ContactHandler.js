/**
 * Contact Handler - Node.js Implementation
 * จัดการข้อมูลบุคลากรด้วย JavaScript
 */

const moment = require('moment');

class ContactHandler {
  constructor(sheetsService, aiProcessor) {
    this.sheetsService = sheetsService;
    this.aiProcessor = aiProcessor;

    // Thai rank patterns
    this.RANK_PATTERNS = [
      'พ\\.ต\\.อ\\.', 'พตอ', 'พ\\.ต\\.ท\\.', 'พตท', 'พ\\.ต\\.ต\\.', 'พตต',
      'ร\\.ต\\.อ\\.', 'รตอ', 'ร\\.ต\\.ท\\.', 'รตท', 'ร\\.ต\\.ต\\.', 'รตต',
      'ด\\.ต\\.', 'ดต', 'จ\\.ส\\.ต\\.', 'จสต', 'ส\\.ต\\.อ\\.', 'สตอ',
      'ส\\.ต\\.ท\\.', 'สตท', 'ส\\.ต\\.ต\\.', 'สตต', 'ร\\.ด\\.ต\\.', 'รดต',
      'ต\\.ต\\.', 'ค\\.ต\\.', 'ร\\.ค\\.ต\\.', 'รคต', 'จ\\.ส\\.ค\\.', 'จสค',
      'ส\\.ต\\.ด\\.', 'สตด', 'นาย', 'นาง', 'นางสาว', 'น\\.ส\\.'
    ];

    // Phone number patterns
    this.PHONE_PATTERNS = [
      '\\b0[0-9]{1,2}[- ]?[0-9]{3}[- ]?[0-9]{4}\\b',  // 081-234-5678
      '\\b[0-9]{3}[- ]?[0-9]{4}\\b',                    // 234-5678
      '\\b[0-9]{2}[- ]?[0-9]{3}[- ]?[0-9]{4}\\b'       // 02-123-4567
    ];

    // Agency patterns
    this.AGENCY_PATTERNS = [
      'สภ\\.[^\\s]*', 'สถานีตำรวจ[^\\s]*', 'กอง[^\\s]*',
      'ฝ่าย[^\\s]*', 'แผนก[^\\s]*', 'กลุ่ม[^\\s]*'
    ];

    // ID Card patterns
    this.ID_PATTERNS = [
      '\\b[0-9]{1}-?[0-9]{4}-?[0-9]{5}-?[0-9]{2}-?[0-9]{1}\\b',
      '\\b[0-9]{13}\\b'
    ];
  }

  async processMessage(text, userId) {
    try {
      console.log(`Processing contact message: ${text.substring(0, 50)}...`);

      // Extract contact information
      const contactData = await this.extractContactInfo(text);

      if (!contactData.isContact) {
        return {
          success: false,
          message: 'ข้อความนี้ไม่ใช่ข้อมูลบุคลากร'
        };
      }

      // Validate required fields
      if (!contactData.Name || contactData.Name.length < 2) {
        return {
          success: false,
          message: '❌ กรุณาระบุชื่อ-นามสกุลให้ชัดเจน'
        };
      }

      // Save to Google Sheets
      const saveResult = await this.sheetsService.appendData('Contacts', contactData);

      if (saveResult.success) {
        let response = `✅ **บันทึกข้อมูลบุคลากรสำเร็จ**\n\n`;
        response += `👤 **ชื่อ:** ${contactData.Name}\n`;
        if (contactData.Position) response += `🎖️ **ตำแหน่ง:** ${contactData.Position}\n`;
        if (contactData.Phone) response += `📞 **โทร:** ${contactData.Phone}\n`;
        if (contactData.Agency) response += `🏢 **สังกัด:** ${contactData.Agency}\n`;
        if (contactData.IDCard) response += `🆔 **บัตรประชาชน:** ${contactData.IDCard}\n`;

        response += `\n⏰ **บันทึกเมื่อ:** ${moment().format('DD/MM/YYYY HH:mm')}`;

        return {
          success: true,
          message: response
        };
      } else {
        return {
          success: false,
          message: `❌ บันทึกไม่สำเร็จ: ${saveResult.error}`
        };
      }

    } catch (error) {
      console.error('Error processing contact message:', error);
      return {
        success: false,
        message: '❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูลบุคลากร'
      };
    }
  }

  async extractContactInfo(text) {
    try {
      const contactData = {
        isContact: false,
        Name: '',
        Position: '',
        Callsign: '',
        Phone: '',
        Agency: '',
        IDCard: '',
        Birthday: '',
        Bank: '',
        Account: ''
      };

      // Check if this looks like contact information
      const hasPersonIndicators = this.hasPersonIndicators(text);
      if (!hasPersonIndicators) {
        return contactData;
      }

      contactData.isContact = true;

      // Extract name and rank/position
      const nameInfo = this.extractNameAndRank(text);
      contactData.Name = nameInfo.name;
      contactData.Position = nameInfo.rank;

      // Extract phone number
      contactData.Phone = this.extractPhone(text);

      // Extract agency/department
      contactData.Agency = this.extractAgency(text);

      // Extract ID card number
      contactData.IDCard = this.extractIDCard(text);

      // Extract callsign
      contactData.Callsign = this.extractCallsign(text);

      // Extract birthday
      contactData.Birthday = this.extractBirthday(text);

      // Extract bank info
      const bankInfo = this.extractBankInfo(text);
      contactData.Bank = bankInfo.bank;
      contactData.Account = bankInfo.account;

      return contactData;

    } catch (error) {
      console.error('Error extracting contact info:', error);
      return { isContact: false };
    }
  }

  hasPersonIndicators(text) {
    const indicators = [
      // Ranks and titles
      ...this.RANK_PATTERNS,
      // Common words in personnel data
      'โทร', 'เบอร์', 'โทรศัพท์', 'บัตรประชาชน', 'เลขบัตร',
      'เกิด', 'วันเกิด', 'สังกัด', 'ตำแหน่ง', 'ชื่อ'
    ];

    const pattern = new RegExp(indicators.join('|'), 'i');
    return pattern.test(text);
  }

  extractNameAndRank(text) {
    try {
      // Pattern to match rank + name
      const rankPattern = new RegExp(`(${this.RANK_PATTERNS.join('|')})\\s*([ก-๙\\s]+)`, 'i');
      const match = text.match(rankPattern);

      if (match) {
        const rank = match[1].trim();
        const name = match[2].trim().split(/\s+/).slice(0, 3).join(' '); // Take first 3 words as name

        return {
          rank: rank,
          name: name
        };
      }

      // If no rank found, try to extract just the name
      const namePattern = /(นาย|นาง|นางสาว|น\.ส\.)\s*([ก-๙\s]+)/i;
      const nameMatch = text.match(namePattern);

      if (nameMatch) {
        return {
          rank: nameMatch[1],
          name: nameMatch[2].trim().split(/\s+/).slice(0, 3).join(' ')
        };
      }

      // Last resort: try to find Thai name pattern
      const thaiNamePattern = /([ก-๙]{2,}\s+[ก-๙]{2,})/;
      const thaiNameMatch = text.match(thaiNamePattern);

      if (thaiNameMatch) {
        return {
          rank: '',
          name: thaiNameMatch[1].trim()
        };
      }

      return { rank: '', name: '' };

    } catch (error) {
      console.error('Error extracting name and rank:', error);
      return { rank: '', name: '' };
    }
  }

  extractPhone(text) {
    try {
      for (const pattern of this.PHONE_PATTERNS) {
        const regex = new RegExp(pattern);
        const match = text.match(regex);
        if (match) {
          // Clean up the phone number
          return match[0].replace(/[-\s]/g, '');
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting phone:', error);
      return '';
    }
  }

  extractAgency(text) {
    try {
      for (const pattern of this.AGENCY_PATTERNS) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[0];
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting agency:', error);
      return '';
    }
  }

  extractIDCard(text) {
    try {
      for (const pattern of this.ID_PATTERNS) {
        const regex = new RegExp(pattern);
        const match = text.match(regex);
        if (match) {
          return match[0].replace(/-/g, '');
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting ID card:', error);
      return '';
    }
  }

  extractCallsign(text) {
    try {
      // Common callsign patterns for police
      const patterns = [
        'รหัส[\\s]*([ก-๙0-9]+)',
        'สัญญาณ[\\s]*([ก-๙0-9]+)',
        'เรียกขาน[\\s]*([ก-๙0-9]+)'
      ];

      for (const pattern of patterns) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1];
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting callsign:', error);
      return '';
    }
  }

  extractBirthday(text) {
    try {
      // Date patterns
      const patterns = [
        '(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})',     // DD/MM/YYYY
        '(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2})',     // DD/MM/YY
        'เกิด[\\s]*(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})',
        'วันเกิด[\\s]*(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})'
      ];

      for (const pattern of patterns) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[match.length - 1]; // Get the last capture group or full match
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting birthday:', error);
      return '';
    }
  }

  extractBankInfo(text) {
    try {
      const banks = ['กสิกร', 'กรุงเทพ', 'ไทยพาณิชย์', 'กรุงไทย', 'ทหารไทย', 'อาคารสงเคราะห์'];
      const result = { bank: '', account: '' };

      // Find bank name
      for (const bank of banks) {
        if (text.includes(bank)) {
          result.bank = bank;
          break;
        }
      }

      // Find account number
      const accountPattern = /(?:บัญชี|เลขบัญชี)[\\s]*([0-9-]+)/i;
      const match = text.match(accountPattern);
      if (match) {
        result.account = match[1].replace(/-/g, '');
      }

      return result;
    } catch (error) {
      console.error('Error extracting bank info:', error);
      return { bank: '', account: '' };
    }
  }

  async searchContacts(query) {
    try {
      const results = await this.sheetsService.searchSheet('Contacts', query.toLowerCase());
      return {
        success: true,
        results: results,
        count: results.length
      };
    } catch (error) {
      console.error('Error searching contacts:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async updateContact(contactId, updates) {
    try {
      const result = await this.sheetsService.updateData('Contacts', contactId, updates);
      return result;
    } catch (error) {
      console.error('Error updating contact:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async deleteContact(contactId) {
    try {
      const result = await this.sheetsService.deleteData('Contacts', contactId);
      return result;
    } catch (error) {
      console.error('Error deleting contact:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Utility method for formatting contact info
  formatContactInfo(contact) {
    let formatted = '';
    if (contact.Name) formatted += `👤 ${contact.Name}\n`;
    if (contact.Position) formatted += `🎖️ ${contact.Position}\n`;
    if (contact.Phone) formatted += `📞 ${contact.Phone}\n`;
    if (contact.Agency) formatted += `🏢 ${contact.Agency}\n`;
    if (contact.IDCard) formatted += `🆔 ${contact.IDCard}\n`;
    return formatted.trim();
  }
}

module.exports = ContactHandler;