/**
 * Order Handler - Node.js Implementation
 * จัดการคำสั่ง/ภารกิจด้วย JavaScript
 */

const moment = require('moment');

class OrderHandler {
  constructor(sheetsService) {
    this.sheetsService = sheetsService;

    // Order/Command patterns
    this.ORDER_KEYWORDS = [
      'คำสั่ง', 'ภารกิจ', 'ให้', 'มอบหมาย', 'สั่งการ',
      'ตรวจ', 'ไป', 'ทำ', 'ดำเนินการ', 'ปฏิบัติ'
    ];

    this.URGENCY_KEYWORDS = {
      'เร่งด่วน': ['เร่งด่วน', 'ด่วนที่สุด', 'เร่ง', 'รีบ', 'ทันที'],
      'ปกติ': ['ปกติ', 'ธรรมดา'],
      'ต่ำ': ['ไม่เร่งด่วน', 'ค่อยๆ', 'เมื่อว่าง']
    };

    this.TIME_PATTERNS = [
      '(\\d{1,2})[:.]?(\\d{2})',                    // 14:30, 14.30
      'ภายใน[\\s]*(\\d{1,2})[\\s]*(?:นาฬิกา|โมง)', // ภายใน 18 นาฬิกา
      'กำหนด[\\s]*(\\d{1,2})[\\s]*(?:นาฬิกา|โมง)', // กำหนด 15 นาฬิกา
      'เวลา[\\s]*(\\d{1,2})[:.]?(\\d{2})',         // เวลา 14:30
    ];

    this.DATE_PATTERNS = [
      '(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2,4})',    // 30/03/2567
      'วันที่[\\s]*(\\d{1,2})[/-](\\d{1,2})',      // วันที่ 30/03
      'ภายในวันที่[\\s]*(\\d{1,2})[/-](\\d{1,2})', // ภายในวันที่ 30/03
    ];
  }

  async processMessage(text, userId) {
    try {
      console.log(`Processing order message: ${text.substring(0, 50)}...`);

      // Extract order information
      const orderData = await this.extractOrderInfo(text);

      if (!orderData.isOrder) {
        return {
          success: false,
          message: 'ข้อความนี้ไม่ใช่คำสั่งหรือภารกิจ'
        };
      }

      // Validate required fields
      if (!orderData.Detail || orderData.Detail.length < 5) {
        return {
          success: false,
          message: '❌ กรุณาระบุรายละเอียดคำสั่งให้ชัดเจน'
        };
      }

      // Save to Google Sheets
      const saveResult = await this.sheetsService.appendData('Orders', orderData);

      if (saveResult.success) {
        let response = `✅ **บันทึกคำสั่ง/ภารกิจสำเร็จ**\n\n`;
        response += `📋 **รายละเอียด:** ${orderData.Detail}\n`;
        if (orderData.Commander) response += `👨‍💼 **ผู้สั่ง:** ${orderData.Commander}\n`;
        if (orderData.Deadline) response += `⏰ **กำหนดเวลา:** ${orderData.Deadline}\n`;
        if (orderData.Urgency) response += `🚨 **ความเร่งด่วน:** ${orderData.Urgency}\n`;
        if (orderData.Note) response += `📝 **หมายเหตุ:** ${orderData.Note}\n`;

        response += `\n📊 **สถานะ:** ${orderData.Status}`;
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
      console.error('Error processing order message:', error);
      return {
        success: false,
        message: '❌ เกิดข้อผิดพลาดในการประมวลผลคำสั่ง'
      };
    }
  }

  async extractOrderInfo(text) {
    try {
      const orderData = {
        isOrder: false,
        Detail: '',
        Commander: '',
        Deadline: '',
        Status: 'Pending',
        Urgency: 'ปกติ',
        Note: ''
      };

      // Check if this looks like an order/command
      const hasOrderIndicators = this.hasOrderIndicators(text);
      if (!hasOrderIndicators) {
        return orderData;
      }

      orderData.isOrder = true;

      // Extract main detail (the core command)
      orderData.Detail = this.extractOrderDetail(text);

      // Extract commander (who gave the order)
      orderData.Commander = this.extractCommander(text);

      // Extract deadline
      orderData.Deadline = this.extractDeadline(text);

      // Extract urgency
      orderData.Urgency = this.extractUrgency(text);

      // Extract additional notes
      orderData.Note = this.extractNotes(text);

      return orderData;

    } catch (error) {
      console.error('Error extracting order info:', error);
      return { isOrder: false };
    }
  }

  hasOrderIndicators(text) {
    const pattern = new RegExp(this.ORDER_KEYWORDS.join('|'), 'i');
    return pattern.test(text);
  }

  extractOrderDetail(text) {
    try {
      // Remove common prefixes to get the main content
      let detail = text;

      const prefixes = [
        'คำสั่ง[:\\s]*',
        'ภารกิจ[:\\s]*',
        'ให้[\\s]*',
        'มอบหมาย[:\\s]*'
      ];

      for (const prefix of prefixes) {
        const regex = new RegExp(prefix, 'i');
        detail = detail.replace(regex, '').trim();
      }

      // Take the main part (usually the first sentence)
      const sentences = detail.split(/[.!?]/);
      return sentences[0].trim().substring(0, 200); // Limit length

    } catch (error) {
      console.error('Error extracting order detail:', error);
      return text.substring(0, 100);
    }
  }

  extractCommander(text) {
    try {
      const patterns = [
        '(?:จาก|โดย|สั่งโดย)[\\s]*([ก-๙\\s]+?)(?:\\s|$)',
        '([ก-๙]+[\\s]*(?:สั่ง|มอบหมาย))',
        '(ผบ\\.[ก-๙\\s]*)',
        '(นาย[ก-๙\\s]*?)(?:สั่ง|ให้)',
      ];

      for (const pattern of patterns) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1].trim().split(/\s+/).slice(0, 3).join(' ');
        }
      }

      return '';
    } catch (error) {
      console.error('Error extracting commander:', error);
      return '';
    }
  }

  extractDeadline(text) {
    try {
      // Try to extract time first
      for (const pattern of this.TIME_PATTERNS) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          const hours = match[1];
          const minutes = match[2] || '00';
          return `${hours}:${minutes}`;
        }
      }

      // Try to extract date
      for (const pattern of this.DATE_PATTERNS) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          const day = match[1];
          const month = match[2];
          const year = match[3] || new Date().getFullYear();
          return `${day}/${month}/${year}`;
        }
      }

      // Look for relative time expressions
      const relativePatterns = [
        'วันนี้', 'พรุ่งนี้', 'มะรืนนี้', 'สัปดาห์นี้', 'เดือนนี้'
      ];

      for (const rel of relativePatterns) {
        if (text.includes(rel)) {
          return rel;
        }
      }

      return '';
    } catch (error) {
      console.error('Error extracting deadline:', error);
      return '';
    }
  }

  extractUrgency(text) {
    try {
      const textLower = text.toLowerCase();

      for (const [urgency, keywords] of Object.entries(this.URGENCY_KEYWORDS)) {
        for (const keyword of keywords) {
          if (textLower.includes(keyword.toLowerCase())) {
            return urgency;
          }
        }
      }

      return 'ปกติ'; // Default
    } catch (error) {
      console.error('Error extracting urgency:', error);
      return 'ปกติ';
    }
  }

  extractNotes(text) {
    try {
      const notePatterns = [
        'หมายเหตุ[:\\s]*(.+)',
        'บันทึก[:\\s]*(.+)',
        'เพิ่มเติม[:\\s]*(.+)',
        'ข้อสังเกต[:\\s]*(.+)'
      ];

      for (const pattern of notePatterns) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1].trim().substring(0, 100);
        }
      }

      return '';
    } catch (error) {
      console.error('Error extracting notes:', error);
      return '';
    }
  }

  async searchOrders(query) {
    try {
      const results = await this.sheetsService.searchSheet('Orders', query.toLowerCase());
      return {
        success: true,
        results: results,
        count: results.length
      };
    } catch (error) {
      console.error('Error searching orders:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async updateOrderStatus(orderId, status) {
    try {
      const result = await this.sheetsService.updateData('Orders', orderId, { Status: status });
      return result;
    } catch (error) {
      console.error('Error updating order status:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  formatOrderInfo(order) {
    let formatted = '';
    if (order.Detail) formatted += `📋 ${order.Detail}\n`;
    if (order.Commander) formatted += `👨‍💼 ${order.Commander}\n`;
    if (order.Deadline) formatted += `⏰ ${order.Deadline}\n`;
    if (order.Urgency) formatted += `🚨 ${order.Urgency}\n`;
    if (order.Status) formatted += `📊 ${order.Status}\n`;
    return formatted.trim();
  }
}

module.exports = OrderHandler;