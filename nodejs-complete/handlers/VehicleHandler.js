/**
 * Vehicle Handler - Node.js Implementation
 * จัดการข้อมูลยานพาหนะด้วย JavaScript
 */

const moment = require('moment');

class VehicleHandler {
  constructor(sheetsService) {
    this.sheetsService = sheetsService;

    // Vehicle patterns
    this.SHIELD_PATTERNS = [
      'โล่[\\s]*([0-9]+)',
      'หมายเลขโล่[\\s]*([0-9]+)',
      'เลขโล่[\\s]*([0-9]+)'
    ];

    this.PLATE_PATTERNS = [
      '([ก-ฮ]{1,2}[\\s]*[0-9]{1,4})',           // กข-1234
      'ทะเบียน[\\s]*([ก-ฮ0-9\\s-]+)',          // ทะเบียน กข-1234
      'เลขทะเบียน[\\s]*([ก-ฮ0-9\\s-]+)'        // เลขทะเบียน กข-1234
    ];

    this.BRAND_PATTERNS = [
      'Toyota', 'Honda', 'Mazda', 'Ford', 'Chevrolet', 'Mitsubishi',
      'Nissan', 'Suzuki', 'Yamaha', 'Kawasaki', 'BMW', 'Mercedes'
    ];

    this.VEHICLE_TYPES = [
      'รถยนต์', 'รถจักรยานยนต์', 'รถบรรทุก', 'รถตู้', 'รถกระบะ',
      'มอเตอร์ไซค์', 'รถแท็กซี่', 'รถสามล้อ'
    ];
  }

  async processMessage(text, userId) {
    try {
      console.log(`Processing vehicle message: ${text.substring(0, 50)}...`);

      // Extract vehicle information
      const vehicleData = await this.extractVehicleInfo(text);

      if (!vehicleData.isVehicle) {
        return {
          success: false,
          message: 'ข้อความนี้ไม่ใช่ข้อมูลยานพาหนะ'
        };
      }

      // Validate required fields
      if (!vehicleData.Shield && !vehicleData.Plate) {
        return {
          success: false,
          message: '❌ กรุณาระบุหมายเลขโล่หรือทะเบียนรถ'
        };
      }

      // Save to Google Sheets
      const saveResult = await this.sheetsService.appendData('Vehicles', vehicleData);

      if (saveResult.success) {
        let response = `✅ **บันทึกข้อมูลยานพาหนะสำเร็จ**\n\n`;
        if (vehicleData.Shield) response += `🛡️ **หมายเลขโล่:** ${vehicleData.Shield}\n`;
        if (vehicleData.Plate) response += `🚗 **ทะเบียน:** ${vehicleData.Plate}\n`;
        if (vehicleData.Brand) response += `🏭 **ยี่ห้อ:** ${vehicleData.Brand}\n`;
        if (vehicleData.User) response += `👤 **ผู้ใช้:** ${vehicleData.User}\n`;
        if (vehicleData.Status) response += `📊 **สถานะ:** ${vehicleData.Status}\n`;

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
      console.error('Error processing vehicle message:', error);
      return {
        success: false,
        message: '❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูลยานพาหนะ'
      };
    }
  }

  async extractVehicleInfo(text) {
    try {
      const vehicleData = {
        isVehicle: false,
        ID: '',
        Shield: '',
        Plate: '',
        Brand: '',
        User: '',
        Repair: '',
        Status: 'ใช้งานได้'
      };

      // Check if this looks like vehicle information
      const hasVehicleIndicators = this.hasVehicleIndicators(text);
      if (!hasVehicleIndicators) {
        return vehicleData;
      }

      vehicleData.isVehicle = true;

      // Extract shield number
      vehicleData.Shield = this.extractShield(text);

      // Extract plate number
      vehicleData.Plate = this.extractPlate(text);

      // Extract brand
      vehicleData.Brand = this.extractBrand(text);

      // Extract user
      vehicleData.User = this.extractUser(text);

      // Extract status
      vehicleData.Status = this.extractStatus(text);

      // Generate ID if not present
      vehicleData.ID = vehicleData.Shield || vehicleData.Plate || `V-${Date.now()}`;

      return vehicleData;

    } catch (error) {
      console.error('Error extracting vehicle info:', error);
      return { isVehicle: false };
    }
  }

  hasVehicleIndicators(text) {
    const indicators = [
      'โล่', 'ทะเบียน', 'รถ', 'หมายเลขโล่', 'เลขโล่',
      ...this.BRAND_PATTERNS,
      ...this.VEHICLE_TYPES,
      // Common license plate patterns
      '[ก-ฮ]{1,2}[\\s]*[0-9]{1,4}',
      // Shield number patterns
      'โล่[\\s]*[0-9]+'
    ];

    const pattern = new RegExp(indicators.join('|'), 'i');
    return pattern.test(text);
  }

  extractShield(text) {
    try {
      for (const pattern of this.SHIELD_PATTERNS) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1].trim();
        }
      }
      return '';
    } catch (error) {
      console.error('Error extracting shield:', error);
      return '';
    }
  }

  extractPlate(text) {
    try {
      for (const pattern of this.PLATE_PATTERNS) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1].trim().replace(/\s+/g, ' ');
        }
      }

      // Try simple pattern
      const simplePattern = /([ก-ฮ]{1,2}[\s-]*[0-9]{1,4})/;
      const simpleMatch = text.match(simplePattern);
      if (simpleMatch) {
        return simpleMatch[1].trim();
      }

      return '';
    } catch (error) {
      console.error('Error extracting plate:', error);
      return '';
    }
  }

  extractBrand(text) {
    try {
      for (const brand of this.BRAND_PATTERNS) {
        const regex = new RegExp(brand, 'i');
        if (regex.test(text)) {
          return brand;
        }
      }

      // Try to find Thai brand names
      const thaiBrands = ['โตโยต้า', 'ฮอนด้า', 'มาสด้า', 'ฟอร์ด', 'มิตซูบิชิ'];
      for (const brand of thaiBrands) {
        if (text.includes(brand)) {
          return brand;
        }
      }

      return '';
    } catch (error) {
      console.error('Error extracting brand:', error);
      return '';
    }
  }

  extractUser(text) {
    try {
      // Patterns to find user/assigned person
      const patterns = [
        'ผู้ใช้[\\s]*([ก-๙\\s]+)',
        'ใช้โดย[\\s]*([ก-๙\\s]+)',
        'มอบหมายให้[\\s]*([ก-๙\\s]+)',
        'สังกัด[\\s]*([ก-๙\\s]+)'
      ];

      for (const pattern of patterns) {
        const regex = new RegExp(pattern, 'i');
        const match = text.match(regex);
        if (match) {
          return match[1].trim().split(/\s+/).slice(0, 3).join(' '); // Take first 3 words
        }
      }

      return '';
    } catch (error) {
      console.error('Error extracting user:', error);
      return '';
    }
  }

  extractStatus(text) {
    try {
      const statusMap = {
        'ใช้งานได้': ['ปกติ', 'ใช้งานได้', 'พร้อมใช้', 'สภาพดี'],
        'ซ่อม': ['ซ่อม', 'เสีย', 'ชำรุด', 'ซ่อมแซม'],
        'จำหน่าย': ['จำหน่าย', 'ยกเลิก', 'หมดอายุ'],
        'ไม่ใช้งาน': ['ไม่ใช้', 'จอด', 'เก็บ']
      };

      const textLower = text.toLowerCase();

      for (const [status, keywords] of Object.entries(statusMap)) {
        for (const keyword of keywords) {
          if (textLower.includes(keyword.toLowerCase())) {
            return status;
          }
        }
      }

      return 'ใช้งานได้'; // Default status
    } catch (error) {
      console.error('Error extracting status:', error);
      return 'ใช้งานได้';
    }
  }

  async searchVehicles(query) {
    try {
      const results = await this.sheetsService.searchSheet('Vehicles', query.toLowerCase());
      return {
        success: true,
        results: results,
        count: results.length
      };
    } catch (error) {
      console.error('Error searching vehicles:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  formatVehicleInfo(vehicle) {
    let formatted = '';
    if (vehicle.Shield) formatted += `🛡️ โล่ ${vehicle.Shield}\n`;
    if (vehicle.Plate) formatted += `🚗 ${vehicle.Plate}\n`;
    if (vehicle.Brand) formatted += `🏭 ${vehicle.Brand}\n`;
    if (vehicle.User) formatted += `👤 ${vehicle.User}\n`;
    if (vehicle.Status) formatted += `📊 ${vehicle.Status}\n`;
    return formatted.trim();
  }
}

module.exports = VehicleHandler;