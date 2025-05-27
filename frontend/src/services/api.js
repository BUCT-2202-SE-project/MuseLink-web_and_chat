// 导入axios请求工具
import axios from 'axios';

const baseURL = '/api';


// 创建axios实例
const api = axios.create({
  baseURL: baseURL,
  // headers: {
  //   'Content-Type': 'application/json'
  // }
});


export const chatAPI = {

  // 新建对话
  async createNewChat(userId, historyName) {
    try {
      
      if (!userId) {
        throw new Error('userId is required');
      }

      // 使用 URLSearchParams 构造 x-www-form-urlencoded 数据
      const params = new URLSearchParams();
      params.append('userId', userId);
      params.append('historyName', historyName);

      // 发起 POST 请求
      const response = await api.post(`/qa/create`, params);
      
      if (response.data.code !== 0) {
        throw new Error(`API Error: ${response.data.message}`);
      }

      return response.data.data;
    } catch (error) {
      console.error('Create chat error:', error);
      throw error;
    }
  },

  // 重命名对话
  async renameChat(historyId, newName) {
    try {
      if (!historyId) {
        throw new Error('historyId is required');
      }
      if (!newName) {
        throw new Error('newName is required');
      }

      // 使用 URLSearchParams 构造 x-www-form-urlencoded 数据
      const params = new URLSearchParams();
      params.append('historyId', historyId);
      params.append('newName', newName);

      // 发起 PATCH 请求
      const response = await api.patch(`/qa/rename`, params);

      if (response.data.code !== 0) {
        throw new Error(`API Error: ${response.data.message}`);
      }

      return response.data.data;
    } catch (error) {
      console.error('Rename chat error:', error);
      throw error;
    }
  },

  // 删除对话
  async deleteChat(historyId) {
    try {
      if (!historyId) {
        throw new Error('historyId is required');
      }

      // 使用 URLSearchParams 构造参数
      const params = new URLSearchParams();
      params.append('historyId', historyId);

      // 发起 DELETE 请求
      const response = await api.delete(`/qa/delete?${params.toString()}`);

      if (response.data.code !== 0) {
        throw new Error(`API Error: ${response.data.message}`);
      }

      return response.data.data;
    } catch (error) {
      console.error('Delete chat error:', error);
      throw error;
    }
  },

  // 发送聊天消息（2.0版本）
  async sendMessage(data, historyId, rag) {
    try {
      let url = `/qa/chat`;
      let params = {};

      if (historyId) {
        params.historyId = historyId;
      }
      
      params.rag = rag;

      // 构造URL查询参数
      const queryString = Object.keys(params)
        .map(key => `${key}=${encodeURIComponent(params[key])}`)
        .join('&');
      
      // 添加基础URL前缀
      const fullUrl = queryString 
        ? `${baseURL}${url}?${queryString}` 
        : `${baseURL}${url}`;
      
      // 准备请求数据
      let requestData;
      if (data instanceof FormData) {
        requestData = data;
      } else {
        requestData = new URLSearchParams();
        requestData.append('question', data);
      }
      
      const headers = {};
      
      // 设置请求头
      if (data instanceof FormData) {
        // 使用FormData时不要手动设置Content-Type，让浏览器自动设置
      } else {
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
      }
      
      // 发送请求
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers,
        body: requestData,
        credentials: 'include' // 确保发送凭证
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      // 创建一个用于处理流数据的方法，可以检测reference信息
      return {
        reader,
        referenceInfo: { value: null }, // 引用对象，用于存储reference值
        async read(callback) {
          let buffer = '';
          let referenceFound = false;
          let accumulatedContent = ''; // 添加累积内容变量
          
          try {
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) break;
              
              // 解码接收到的数据
              const chunk = new TextDecoder().decode(value);
              buffer += chunk;
              accumulatedContent += chunk; // 累积所有内容
              
              // 检查是否包含reference信息
              const referenceMatch = buffer.match(/<!-- REFERENCE_DATA:([\s\S]*?) -->/);
              if (referenceMatch) {
                // 提取reference信息
                this.referenceInfo.value = referenceMatch[1].trim();
                // 从累积内容和当前缓冲区中移除reference标记
                accumulatedContent = accumulatedContent.replace(/<!-- REFERENCE_DATA:([\s\S]*?) -->/, '');
                // 移除reference标记
                buffer = buffer.replace(/<!-- REFERENCE_DATA:([\s\S]*?) -->/, '');
                referenceFound = true;
              }
              
              // 回调提供处理后的内容
              callback({
                content: accumulatedContent,
                done: false,
                referenceFound,
                reference: this.referenceInfo.value
              });
              
              // 清空已处理的缓冲区
              buffer = '';
            }
            
            // 流结束
            callback({
              content: accumulatedContent,
              done: true,
              referenceFound,
              reference: this.referenceInfo.value
            });
          } catch (error) {
            console.error('Error reading stream:', error);
            throw error;
          }
        }
      };
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // 获取聊天记录列表
  async getChatHistory(userId) {
    try {
      // 检查是否传入了userId
      // let url = `/qa/getHistoryList`;
      let url = `/qa/getHistoryList`;
      if (userId) {
        // 将userId作为查询参数添加到URL
        url = `${url}?userId=${encodeURIComponent(userId)}`;
      }
      
      const response = await api.get(url);
      
      if (response.data.code !== 0) {
        throw new Error(`API Error: ${response.data.message}`);
      }

      // 转换为前端需要的格式
      return response.data.data.map(item => ({
        id: item.historyId,
        title: item.historyName
      }));
    } catch (error) {
      console.error('API Error:', error);
      return [];
    }
  },

  // 获取特定对话的消息历史
  async getChatMessages(chatId) {
    try {
      // 构造请求URL，使用新的getHistoryInfo接口
      const response = await api.get(`/qa/getHistoryInfo?historyId=${chatId}`);

      // 检查响应状态
      if (response.data.code !== 0) {
        throw new Error(`API Error: ${response.data.message}`);
      }
      
      // 转换数据格式为ChatMessage组件期望的格式
      const messages = [];
      response.data.data.forEach(item => {
        // 添加用户消息
        messages.push({
          role: 'user',
          content: item.question,
          timestamp: new Date() // 使用当前时间作为临时时间戳
        });
        
        // 添加助手消息
        messages.push({
          role: 'assistant',
          content: item.answer,
          reference: item.reference, // 添加reference字段
          timestamp: new Date(new Date().getTime() + 1000) // 比用户消息晚1秒
        });
      });
      
      
      return messages;
    } catch (error) {
      console.error('获取聊天消息失败:', error);
      return [];
    }
  }

}