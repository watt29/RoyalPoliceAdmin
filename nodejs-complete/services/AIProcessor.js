/**
 * AI Processor - Node.js Implementation
 * ประมวลผล AI และ Natural Language Processing
 */

class AIProcessor {
  constructor() {
    this.intentPatterns = {
      contact: {
        keywords: ['นาย', 'นาง', 'นางสาว', 'พ.ต.', 'ร.ต.', 'จส.ต.', 'โทร', 'เบอร์', 'สภ.'],
        patterns: [
          /(?:นาย|นาง|นางสาว|น\.ส\.)\s*[ก-๙\s]+/i,
          /(?:พ\.ต\.|ร\.ต\.|จส\.ต\.)[ก-๙\s]+/i,
          /โทร[:\s]*[0-9-]+/i
        ],
        confidence: 0.8
      },
      vehicle: {
        keywords: ['โล่', 'ทะเบียน', 'รถ', 'มอเตอร์ไซค์', 'กข', 'นข', 'บข'],
        patterns: [
          /โล่[:\s]*[0-9]+/i,
          /ทะเบียน[:\s]*[ก-ฮ0-9\s-]+/i,
          /[ก-ฮ]{1,2}[\s-]*[0-9]{1,4}/i
        ],
        confidence: 0.8
      },
      order: {
        keywords: ['คำสั่ง', 'ภารกิจ', 'ให้', 'ไป', 'ตรวจ', 'ปฏิบัติ', 'เร่งด่วน'],
        patterns: [
          /ให้[ก-๙\s]+ไป/i,
          /คำสั่ง[:\s]*[ก-๙\s]+/i,
          /เร่งด่วน/i
        ],
        confidence: 0.7
      },
      search: {
        keywords: ['ค้นหา', 'หา', 'ดู', 'เช็ค', 'ตรวจสอบ', 'สอบถาม'],
        patterns: [
          /(?:ค้นหา|หา|ดู)[:\s]*[ก-๙0-9\s]+/i,
          /(?:เช็ค|ตรวจสอบ)[ก-๙0-9\s]+/i
        ],
        confidence: 0.9
      },
      file: {
        keywords: ['สร้าง', 'แก้ไข', 'ลบ', 'อ่าน', 'ไฟล์', 'เอกสาร'],
        patterns: [
          /(?:สร้าง|แก้ไข|ลบ|อ่าน)[:\s]*[a-zA-Z0-9._-]+/i,
          /ไฟล์[:\s]*[a-zA-Z0-9._-]+/i
        ],
        confidence: 0.85
      }
    };

    this.thaiSentiment = {
      positive: ['ดี', 'เยี่ยม', 'ยอดเยี่ยม', 'สำเร็จ', 'เสร็จ', 'โอเค', 'ขอบคุณ'],
      negative: ['แย่', 'ไม่ดี', 'ล้มเหลว', 'ผิดพลาด', 'เสีย', 'ชำรุด', 'ขัดข้อง'],
      neutral: ['ปกติ', 'ธรรมดา', 'เช่นนี้', 'อย่างนี้']
    };
  }

  async detectIntent(text) {
    try {
      if (!text || text.trim().length === 0) {
        return { type: 'general', confidence: 0.1 };
      }

      const textLower = text.toLowerCase();
      let bestMatch = { type: 'general', confidence: 0.0 };

      // Check each intent type
      for (const [intentType, config] of Object.entries(this.intentPatterns)) {
        let score = 0;

        // Keyword matching
        for (const keyword of config.keywords) {
          if (textLower.includes(keyword.toLowerCase())) {
            score += 0.3;
          }
        }

        // Pattern matching
        for (const pattern of config.patterns) {
          if (pattern.test(text)) {
            score += 0.5;
          }
        }

        // Calculate final confidence
        const confidence = Math.min(score, 1.0) * config.confidence;

        if (confidence > bestMatch.confidence) {
          bestMatch = { type: intentType, confidence };
        }
      }

      // Enhanced intent detection using context
      const contextualScore = this.analyzeContext(text);
      bestMatch.confidence = Math.min(bestMatch.confidence + contextualScore, 1.0);

      console.log(`AI Intent Detection: "${text.substring(0, 30)}..." -> ${bestMatch.type} (${(bestMatch.confidence * 100).toFixed(1)}%)`);

      return bestMatch;

    } catch (error) {
      console.error('Error detecting intent:', error);
      return { type: 'general', confidence: 0.2 };
    }
  }

  analyzeContext(text) {
    try {
      let contextScore = 0;

      // Length-based scoring
      if (text.length > 20 && text.length < 200) {
        contextScore += 0.1; // Appropriate length
      }

      // Structure analysis
      if (text.includes(':') || text.includes('=')) {
        contextScore += 0.1; // Structured data
      }

      // Number presence
      if (/[0-9]+/.test(text)) {
        contextScore += 0.1; // Contains numbers (likely data)
      }

      // Thai language confidence
      const thaiChars = (text.match(/[ก-๙]/g) || []).length;
      const totalChars = text.length;
      if (thaiChars / totalChars > 0.5) {
        contextScore += 0.1; // High Thai content
      }

      return Math.min(contextScore, 0.4); // Max additional score

    } catch (error) {
      console.error('Error analyzing context:', error);
      return 0;
    }
  }

  analyzeSentiment(text) {
    try {
      const textLower = text.toLowerCase();
      let sentiment = { type: 'neutral', score: 0.5, confidence: 0.5 };

      let positiveScore = 0;
      let negativeScore = 0;

      // Check positive words
      for (const word of this.thaiSentiment.positive) {
        if (textLower.includes(word)) {
          positiveScore += 1;
        }
      }

      // Check negative words
      for (const word of this.thaiSentiment.negative) {
        if (textLower.includes(word)) {
          negativeScore += 1;
        }
      }

      // Determine sentiment
      if (positiveScore > negativeScore) {
        sentiment = {
          type: 'positive',
          score: 0.7 + (positiveScore * 0.1),
          confidence: Math.min(positiveScore / 3, 1.0)
        };
      } else if (negativeScore > positiveScore) {
        sentiment = {
          type: 'negative',
          score: 0.3 - (negativeScore * 0.1),
          confidence: Math.min(negativeScore / 3, 1.0)
        };
      }

      return sentiment;

    } catch (error) {
      console.error('Error analyzing sentiment:', error);
      return { type: 'neutral', score: 0.5, confidence: 0.3 };
    }
  }

  extractEntities(text) {
    try {
      const entities = {
        persons: [],
        organizations: [],
        locations: [],
        phones: [],
        dates: [],
        numbers: []
      };

      // Person names (with titles)
      const personPattern = /((?:นาย|นาง|นางสาว|พ\.ต\.|ร\.ต\.|จส\.ต\.)[ก-๙\s]+)/g;
      let match;
      while ((match = personPattern.exec(text)) !== null) {
        entities.persons.push(match[1].trim());
      }

      // Organizations
      const orgPattern = /(สภ\.[ก-๙\s]*|กอง[ก-๙\s]*|แผนก[ก-๙\s]*)/g;
      while ((match = orgPattern.exec(text)) !== null) {
        entities.organizations.push(match[1].trim());
      }

      // Phone numbers
      const phonePattern = /(\b0[0-9]{1,2}[- ]?[0-9]{3}[- ]?[0-9]{4}\b)/g;
      while ((match = phonePattern.exec(text)) !== null) {
        entities.phones.push(match[1].replace(/[- ]/g, ''));
      }

      // Dates
      const datePattern = /(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/g;
      while ((match = datePattern.exec(text)) !== null) {
        entities.dates.push(match[1]);
      }

      // Numbers
      const numberPattern = /(\b\d+\b)/g;
      while ((match = numberPattern.exec(text)) !== null) {
        entities.numbers.push(parseInt(match[1]));
      }

      return entities;

    } catch (error) {
      console.error('Error extracting entities:', error);
      return {};
    }
  }

  generateSummary(text, maxLength = 100) {
    try {
      if (text.length <= maxLength) {
        return text;
      }

      // Simple summarization - take first sentence or first part
      const sentences = text.split(/[.!?]/);
      let summary = sentences[0];

      // If first sentence is too short, add more
      if (summary.length < maxLength / 2 && sentences.length > 1) {
        summary += '. ' + sentences[1];
      }

      // Truncate if still too long
      if (summary.length > maxLength) {
        summary = summary.substring(0, maxLength - 3) + '...';
      }

      return summary;

    } catch (error) {
      console.error('Error generating summary:', error);
      return text.substring(0, maxLength) + '...';
    }
  }

  classifyDataType(text) {
    try {
      const intent = this.detectIntent(text);
      const entities = this.extractEntities(text);

      return {
        primaryType: intent.type,
        confidence: intent.confidence,
        entities: entities,
        metadata: {
          length: text.length,
          hasNumbers: /\d/.test(text),
          hasThai: /[ก-๙]/.test(text),
          hasEnglish: /[a-zA-Z]/.test(text),
          wordCount: text.split(/\s+/).length
        }
      };

    } catch (error) {
      console.error('Error classifying data type:', error);
      return { primaryType: 'general', confidence: 0.1 };
    }
  }

  // Simple spell check for common Thai words
  spellCheck(text) {
    try {
      const corrections = {
        'พ.ต.ต': 'พ.ต.ต.',
        'ร.ต.ต': 'ร.ต.ต.',
        'จส.ต': 'จส.ต.',
        'โทรศัทพ์': 'โทรศัพท์',
        'เบอร์โทร': 'เบอร์โทร',
        'ทะเบืยน': 'ทะเบียน'
      };

      let correctedText = text;
      for (const [wrong, correct] of Object.entries(corrections)) {
        correctedText = correctedText.replace(new RegExp(wrong, 'gi'), correct);
      }

      return {
        originalText: text,
        correctedText: correctedText,
        hasCorrections: correctedText !== text
      };

    } catch (error) {
      console.error('Error in spell check:', error);
      return { originalText: text, correctedText: text, hasCorrections: false };
    }
  }
}

module.exports = AIProcessor;