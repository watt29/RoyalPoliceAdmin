/**
 * Data Processor - Node.js Implementation
 * ประมวลผลและวิเคราะห์ข้อมูลขั้นสูง
 */

const moment = require('moment');
const fs = require('fs-extra');
const path = require('path');

class DataProcessor {
  constructor() {
    this.dataCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes

    // Statistics configuration
    this.statsConfig = {
      contacts: {
        groupBy: ['Agency', 'Position'],
        metrics: ['count', 'phoneCount']
      },
      vehicles: {
        groupBy: ['Status', 'Brand'],
        metrics: ['count', 'utilization']
      },
      orders: {
        groupBy: ['Status', 'Urgency', 'Commander'],
        metrics: ['count', 'completionRate']
      }
    };
  }

  // Data validation and cleaning
  validateAndCleanData(data, schema) {
    try {
      const cleaned = { ...data };
      const issues = [];

      for (const [field, rules] of Object.entries(schema)) {
        const value = cleaned[field];

        // Required field check
        if (rules.required && (!value || value.toString().trim().length === 0)) {
          issues.push(`${field} is required`);
          continue;
        }

        if (!value) continue; // Skip optional empty fields

        // Type validation
        if (rules.type) {
          switch (rules.type) {
            case 'phone':
              cleaned[field] = this.cleanPhoneNumber(value);
              if (cleaned[field] && !this.isValidPhoneNumber(cleaned[field])) {
                issues.push(`${field} is not a valid phone number`);
              }
              break;

            case 'idcard':
              cleaned[field] = this.cleanIDCard(value);
              if (cleaned[field] && !this.isValidIDCard(cleaned[field])) {
                issues.push(`${field} is not a valid ID card number`);
              }
              break;

            case 'date':
              cleaned[field] = this.normalizeDate(value);
              if (cleaned[field] && !moment(cleaned[field], 'DD/MM/YYYY').isValid()) {
                issues.push(`${field} is not a valid date`);
              }
              break;

            case 'text':
              cleaned[field] = value.toString().trim();
              if (rules.maxLength && cleaned[field].length > rules.maxLength) {
                cleaned[field] = cleaned[field].substring(0, rules.maxLength);
                issues.push(`${field} was truncated to ${rules.maxLength} characters`);
              }
              break;
          }
        }

        // Pattern validation
        if (rules.pattern && cleaned[field]) {
          const regex = new RegExp(rules.pattern);
          if (!regex.test(cleaned[field])) {
            issues.push(`${field} does not match required pattern`);
          }
        }
      }

      return {
        data: cleaned,
        isValid: issues.length === 0,
        issues: issues
      };

    } catch (error) {
      console.error('Error validating data:', error);
      return {
        data: data,
        isValid: false,
        issues: ['Validation failed due to system error']
      };
    }
  }

  // Phone number utilities
  cleanPhoneNumber(phone) {
    if (!phone) return '';
    return phone.toString().replace(/[^\d]/g, '');
  }

  isValidPhoneNumber(phone) {
    const cleaned = this.cleanPhoneNumber(phone);
    // Thai phone number patterns
    return /^(0[1-9][0-9]{7,8}|[1-9][0-9]{6,7})$/.test(cleaned);
  }

  formatPhoneNumber(phone) {
    const cleaned = this.cleanPhoneNumber(phone);
    if (cleaned.length === 10 && cleaned.startsWith('0')) {
      return `${cleaned.substring(0, 3)}-${cleaned.substring(3, 6)}-${cleaned.substring(6)}`;
    }
    return cleaned;
  }

  // ID Card utilities
  cleanIDCard(idcard) {
    if (!idcard) return '';
    return idcard.toString().replace(/[^\d]/g, '');
  }

  isValidIDCard(idcard) {
    const cleaned = this.cleanIDCard(idcard);
    if (cleaned.length !== 13) return false;

    // Thai ID card checksum validation
    let sum = 0;
    for (let i = 0; i < 12; i++) {
      sum += parseInt(cleaned.charAt(i)) * (13 - i);
    }
    const checkDigit = (11 - (sum % 11)) % 10;
    return checkDigit === parseInt(cleaned.charAt(12));
  }

  formatIDCard(idcard) {
    const cleaned = this.cleanIDCard(idcard);
    if (cleaned.length === 13) {
      return `${cleaned.substring(0, 1)}-${cleaned.substring(1, 5)}-${cleaned.substring(5, 10)}-${cleaned.substring(10, 12)}-${cleaned.substring(12)}`;
    }
    return cleaned;
  }

  // Date utilities
  normalizeDate(dateString) {
    if (!dateString) return '';

    try {
      // Handle various date formats
      const formats = [
        'DD/MM/YYYY',
        'DD-MM-YYYY',
        'D/M/YYYY',
        'D-M-YYYY',
        'DD/MM/YY',
        'DD-MM-YY'
      ];

      for (const format of formats) {
        const parsed = moment(dateString, format, true);
        if (parsed.isValid()) {
          return parsed.format('DD/MM/YYYY');
        }
      }

      // Try parsing with flexible parsing
      const flexible = moment(dateString);
      if (flexible.isValid()) {
        return flexible.format('DD/MM/YYYY');
      }

      return '';

    } catch (error) {
      console.error('Error normalizing date:', error);
      return '';
    }
  }

  // Data analysis and statistics
  async analyzeData(data, type) {
    try {
      const cacheKey = `analysis_${type}_${JSON.stringify(data).length}`;

      // Check cache
      if (this.dataCache.has(cacheKey)) {
        const cached = this.dataCache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.cacheTimeout) {
          return cached.result;
        }
      }

      const analysis = {
        totalRecords: data.length,
        overview: {},
        trends: {},
        insights: []
      };

      if (data.length === 0) {
        return analysis;
      }

      // Basic statistics
      analysis.overview = this.calculateBasicStats(data, type);

      // Grouping analysis
      if (this.statsConfig[type]) {
        analysis.grouping = this.analyzeGrouping(data, this.statsConfig[type]);
      }

      // Trend analysis (if timestamps available)
      analysis.trends = this.analyzeTrends(data);

      // Generate insights
      analysis.insights = this.generateInsights(analysis, type);

      // Cache result
      this.dataCache.set(cacheKey, {
        result: analysis,
        timestamp: Date.now()
      });

      return analysis;

    } catch (error) {
      console.error('Error analyzing data:', error);
      return { error: 'Failed to analyze data', totalRecords: 0 };
    }
  }

  calculateBasicStats(data, type) {
    const stats = {
      count: data.length,
      recentCount: 0,
      oldestRecord: null,
      newestRecord: null
    };

    // Time-based analysis
    const now = moment();
    data.forEach(record => {
      if (record.Timestamp) {
        const recordTime = moment(record.Timestamp, 'DD/MM/YYYY HH:mm');
        if (recordTime.isValid()) {
          if (!stats.oldestRecord || recordTime.isBefore(stats.oldestRecord)) {
            stats.oldestRecord = recordTime.format('DD/MM/YYYY HH:mm');
          }
          if (!stats.newestRecord || recordTime.isAfter(stats.newestRecord)) {
            stats.newestRecord = recordTime.format('DD/MM/YYYY HH:mm');
          }

          // Count recent records (last 7 days)
          if (recordTime.isAfter(now.clone().subtract(7, 'days'))) {
            stats.recentCount++;
          }
        }
      }
    });

    // Type-specific stats
    switch (type) {
      case 'contacts':
        stats.withPhone = data.filter(r => r.Phone).length;
        stats.withAgency = data.filter(r => r.Agency).length;
        break;
      case 'vehicles':
        stats.inUse = data.filter(r => r.Status === 'ใช้งานได้').length;
        stats.underRepair = data.filter(r => r.Status === 'ซ่อม').length;
        break;
      case 'orders':
        stats.pending = data.filter(r => r.Status === 'Pending').length;
        stats.completed = data.filter(r => r.Status === 'Done').length;
        stats.urgent = data.filter(r => r.Urgency === 'เร่งด่วน').length;
        break;
    }

    return stats;
  }

  analyzeGrouping(data, config) {
    const grouping = {};

    config.groupBy.forEach(field => {
      grouping[field] = {};
      data.forEach(record => {
        const value = record[field] || 'ไม่ระบุ';
        grouping[field][value] = (grouping[field][value] || 0) + 1;
      });

      // Sort by count
      grouping[field] = Object.entries(grouping[field])
        .sort(([,a], [,b]) => b - a)
        .reduce((obj, [key, value]) => {
          obj[key] = value;
          return obj;
        }, {});
    });

    return grouping;
  }

  analyzeTrends(data) {
    const trends = {
      daily: {},
      weekly: {},
      monthly: {}
    };

    data.forEach(record => {
      if (record.Timestamp) {
        const recordTime = moment(record.Timestamp, 'DD/MM/YYYY HH:mm');
        if (recordTime.isValid()) {
          // Daily trends
          const day = recordTime.format('DD/MM/YYYY');
          trends.daily[day] = (trends.daily[day] || 0) + 1;

          // Weekly trends
          const week = recordTime.format('YYYY-WW');
          trends.weekly[week] = (trends.weekly[week] || 0) + 1;

          // Monthly trends
          const month = recordTime.format('MM/YYYY');
          trends.monthly[month] = (trends.monthly[month] || 0) + 1;
        }
      }
    });

    return trends;
  }

  generateInsights(analysis, type) {
    const insights = [];

    try {
      // Growth insights
      if (analysis.overview.recentCount > 0) {
        const recentPercentage = (analysis.overview.recentCount / analysis.totalRecords * 100).toFixed(1);
        if (recentPercentage > 30) {
          insights.push(`📈 ข้อมูลใหม่เพิ่มขึ้นเร็ว ${recentPercentage}% ในสัปดาห์ที่ผ่านมา`);
        }
      }

      // Type-specific insights
      switch (type) {
        case 'contacts':
          if (analysis.overview.withPhone / analysis.totalRecords < 0.8) {
            insights.push('📞 ควรเพิ่มข้อมูลเบอร์โทรศัพท์ให้ครบถ้วน');
          }
          break;

        case 'vehicles':
          if (analysis.overview.underRepair > analysis.overview.inUse * 0.2) {
            insights.push('🔧 ยานพาหนะซ่อมมากกว่าปกติ ควรตรวจสอบ');
          }
          break;

        case 'orders':
          if (analysis.overview.pending > analysis.overview.completed) {
            insights.push('📋 งานค้างเยอะ ควรเร่งดำเนินการ');
          }
          if (analysis.overview.urgent > analysis.totalRecords * 0.3) {
            insights.push('🚨 งานเร่งด่วนมากกว่าปกติ');
          }
          break;
      }

      // Data quality insights
      if (analysis.grouping) {
        Object.entries(analysis.grouping).forEach(([field, values]) => {
          const undefinedCount = values['ไม่ระบุ'] || 0;
          if (undefinedCount > analysis.totalRecords * 0.3) {
            insights.push(`⚠️ ข้อมูล ${field} ไม่ครบถ้วน ${((undefinedCount/analysis.totalRecords)*100).toFixed(1)}%`);
          }
        });
      }

    } catch (error) {
      console.error('Error generating insights:', error);
      insights.push('❌ ไม่สามารถสร้างข้อมูลเชิงลึกได้');
    }

    return insights;
  }

  // Export utilities
  async exportToCSV(data, filename) {
    try {
      if (!data || data.length === 0) {
        return { success: false, error: 'No data to export' };
      }

      const headers = Object.keys(data[0]);
      let csv = headers.join(',') + '\n';

      data.forEach(row => {
        const values = headers.map(header => {
          const value = row[header] || '';
          // Escape commas and quotes
          return value.toString().includes(',') ? `"${value.replace(/"/g, '""')}"` : value;
        });
        csv += values.join(',') + '\n';
      });

      const filePath = path.join('./exports', filename);
      await fs.ensureDir('./exports');
      await fs.writeFile(filePath, csv, 'utf8');

      return {
        success: true,
        filePath: filePath,
        filename: filename,
        recordCount: data.length
      };

    } catch (error) {
      console.error('Error exporting to CSV:', error);
      return { success: false, error: error.message };
    }
  }

  // Data deduplication
  findDuplicates(data, compareFields) {
    const duplicates = [];
    const seen = new Map();

    data.forEach((record, index) => {
      const key = compareFields.map(field => record[field] || '').join('|').toLowerCase();

      if (seen.has(key)) {
        duplicates.push({
          original: seen.get(key),
          duplicate: { ...record, index }
        });
      } else {
        seen.set(key, { ...record, index });
      }
    });

    return duplicates;
  }

  // Clear cache
  clearCache() {
    this.dataCache.clear();
    console.log('Data processor cache cleared');
  }
}

module.exports = DataProcessor;