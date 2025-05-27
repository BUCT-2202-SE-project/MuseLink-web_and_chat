<template>
  <div class="ai-chat">
    <div class="chat-container">
      <div class="sidebar">
        <div class="history-header">
          <h2>聊天记录</h2>
          <button class="new-chat" @click="startNewChat">
            <PlusIcon class="icon" />
            新对话
          </button>
        </div>
        <div class="history-list">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="history-item"
            :class="{ 'active': currentChatId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <ChatBubbleLeftRightIcon class="icon" />
            <span class="title">{{ chat.title || '新对话' }}</span>

            <el-dropdown @command="(command) => handleSessionCommand(chat.id, command)" @click.stop>
              <template #default>
                <el-button text @click.stop>
                  <More class="icon" />
                </el-button>
              </template>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      
      <div class="chat-main">
        <div class="messages" ref="messagesRef">
          <ChatMessage
            v-for="(message, index) in currentMessages"
            :key="index"
            :message="message"
            :is-stream="isStreaming && index === currentMessages.length - 1"
            :is-waiting="isWaiting && index === currentMessages.length - 1"
            :is-thinking="isThinking && index === currentMessages.length - 1"
          />
          
          <!-- 常见问题按钮区域 -->
          <div class="quick-questions" v-if="showQuickQuestions">
            <h3>你可能想问：</h3>
            <div class="questions-container">
              <button 
                v-for="(question, index) in commonQuestions" 
                :key="index" 
                class="question-btn"
                @click="handleQuickQuestion(question)"
              >
                {{ question }}
              </button>
            </div>
          </div>
        </div>
        
        <div class="input-area">

          <div class="input-row">
            <!-- 添加RAG按钮 -->
            <el-tooltip
              content="RAG (Retrieval-Augmented Generation)：结合知识库检索的AI回答功能，可提供基于特定数据的更准确回答"
              placement="top"
              effect="light"
              popper-class="rag-tooltip"
            >
              <el-button
                :type="isRagActive ? 'primary' : 'default'"
                round
                size="small"
                @click="toggleRagMode"
                class="rag-button"
              >
                RAG
              </el-button>
            </el-tooltip>
            <textarea
              v-model="userInput"
              @keydown.enter.prevent="sendMessage"
              :placeholder="'输入消息...'"
              rows="1"
              ref="inputRef"
            ></textarea>
            <button 
              class="send-button" 
              @click="sendMessage"
              :disabled="isStreaming || !userInput.trim()"
            >
              <PaperAirplaneIcon class="icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios' // 添加axios引用
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import ChatMessage from '../components/ChatMessage.vue'
import { chatAPI } from '../services/api'
import { ElMessageBox, ElMessage } from 'element-plus'
import { More } from '@element-plus/icons-vue'
import useChatIdStore from '@/stores/chatId.js'

const chatIdStore = useChatIdStore()

// 添加user对象
const user = ref({
  user_id: '',
  username: '',
  email: '',
  avatar: '',
  register_time: '',
  permission_status: '正常'
})

// 添加获取用户信息的方法
const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/user');
    if (response.data.success) {
      user.value = response.data.user;
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
}

const messagesRef = ref(null)
const inputRef = ref(null)
const userInput = ref('')
const isStreaming = ref(false)
const isWaiting = ref(false) // 初始等待状态标志
const isThinking = ref(false) // 思考中状态标志
let outputTimer = null // 用于检测输出暂停的定时器
const outputTimeout = 1000 // 1秒无输出视为暂停

const currentChatId = ref(chatIdStore.chatId || null)
const currentMessages = ref([])
const chatHistory = ref([])


// 添加RAG模式的状态控制
const isRagActive = ref(false)

// RAG模式切换函数
const toggleRagMode = () => {
  isRagActive.value = !isRagActive.value
}

// 自动调整输入框高度
const adjustTextareaHeight = () => {
  const textarea = inputRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = textarea.scrollHeight + 'px'
  }else{
    textarea.style.height = '50px'
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// 发送聊天消息 （3.0版本）（修复消息流式显示过程中切换到其他对话显示错误的BUG）
const sendMessage = async () => {
  if (isStreaming.value) return
  if (!userInput.value.trim()) return
  
  // 发送消息时隐藏常见问题区域
  showQuickQuestions.value = false
  
  const messageContent = userInput.value.trim()
  
  // 添加用户消息
  const userMessage = {
    role: 'user',
    content: messageContent,
    timestamp: new Date()
  }
  currentMessages.value.push(userMessage)
  
  // 清空输入
  userInput.value = ''
  adjustTextareaHeight()
  await scrollToBottom()

  // 保存发送请求时的对话ID，用于后续检查
  let originalChatId = currentChatId.value

  if (!currentChatId.value) {
    try {
      // 创建对话标题，截取前10个字符
      const chatTitle = messageContent.length > 10 ? messageContent.substring(0, 10) + '...' : messageContent;
      
      // 修改API调用，传递用户ID和标题
      const data = await chatAPI.createNewChat(user.value.user_id, chatTitle)
      currentChatId.value = data.historyId  // 获取新对话 ID
      originalChatId = currentChatId.value  // 更新原始ID
      chatIdStore.chatId = currentChatId.value  // 将新对话ID存储到pinia中

      // 将新对话添加到历史记录中
      const newChat = {
        id: data.historyId,
        title: chatTitle
      }
      chatHistory.value = [newChat, ...chatHistory.value]
    } catch (createErr) {
      console.error('创建对话失败:', createErr)
      return
    }
  }
  
  // 准备发送数据
  const formData = new FormData()
  if (messageContent) {
    formData.append('question', messageContent)
  }
  
  // 添加助手消息占位
  const assistantMessage = {
    role: 'assistant',
    content: '',
    reference: '', 
    timestamp: new Date()
  }
  currentMessages.value.push(assistantMessage)
  isStreaming.value = true
  isWaiting.value = true // 设置为等待状态
  isThinking.value = false // 初始化思考状态
  
  try {
    // 获取封装了流处理的对象
    const streamHandler = await chatAPI.sendMessage(formData, originalChatId, isRagActive.value)
    
    // 使用新的回调方式处理流数据
    await streamHandler.read(({ content, done, referenceFound, reference }) => {
      // 检查当前对话ID是否已更改，如果更改了则不更新UI
      if (originalChatId !== currentChatId.value) {
        return; // 用户已切换到其他对话，不更新UI
      }
      
      // 如果是第一次收到数据，关闭等待状态
      if (isWaiting.value && content) {
        isWaiting.value = false
      }
      
      // 重置输出暂停检测定时器
      if (outputTimer) {
        clearTimeout(outputTimer)
      }
      
      // 如果内容包含<think>标签，可能会有后续暂停
      if (content && content.includes('<think>')) {
        // 设置定时器，检测输出暂停
        outputTimer = setTimeout(() => {
          // 如果定时器触发，说明有段时间没有新内容了，显示思考状态
          if (originalChatId === currentChatId.value) {
            isThinking.value = true
          }
        }, outputTimeout)
      } else {
        isThinking.value = false
      }
      
      // 更新助手消息内容
      assistantMessage.content = content
      
      // 如果找到了引用信息，更新它
      if (referenceFound) {
        assistantMessage.reference = reference
      }
      
      // 强制刷新视图
      const lastIndex = currentMessages.value.length - 1
      currentMessages.value.splice(lastIndex, 1, { ...assistantMessage })
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    // 仅在当前对话ID未更改时更新错误消息
    if (originalChatId === currentChatId.value) {
      assistantMessage.content = '抱歉，发生了错误，请稍后重试。'
      isWaiting.value = false // 关闭等待状态
    }
  } finally {
    // 仅在当前对话ID未更改时更新isStreaming状态
    if (originalChatId === currentChatId.value) {
      isStreaming.value = false
      isWaiting.value = false // 确保关闭等待状态
      isThinking.value = false // 确保关闭思考状态
      // 清除可能存在的定时器
      if (outputTimer) {
        clearTimeout(outputTimer)
        outputTimer = null
      }
      await scrollToBottom()
    }
  }
}

// 加载特定对话
const loadChat = async (chatId) => {
  // 如果有一个未使用的新对话（currentChatId为空字符串），则从历史记录中删除它
  if (currentChatId.value === '') {
    chatHistory.value = chatHistory.value.filter(chat => chat.id !== '');
  }
  
  currentChatId.value = chatId;
  chatIdStore.chatId = chatId;  // 将当前对话ID存储到pinia中
  try {
    // 调用修改后的API方法获取消息历史
    const messages = await chatAPI.getChatMessages(chatId);
    currentMessages.value = messages;
    
    // 滚动到底部显示最新消息
    await scrollToBottom();
  } catch (error) {
    console.error('加载对话消息失败:', error);
    ElMessage.error('加载对话消息失败，请稍后重试');
    currentMessages.value = [];
  }
}

// 修改加载聊天历史的API调用，使用user.value.user_id
const loadChatHistory = async () => {
  try {
    const history = await chatAPI.getChatHistory(user.value.user_id)
    chatHistory.value = history?.filter(chat => chat.id !== '') || []
  } catch (error) {
    console.error('加载聊天历史失败:', error)
    chatHistory.value = []
  }
}

// 开始新对话
const startNewChat = () => {
  // 检查是否已经有一个空的新对话
  const hasEmptyChat = chatHistory.value.some(chat => chat.id === '');
  
  // 如果已经有空的新对话，则不再创建
  if (hasEmptyChat && currentChatId.value === '') {
    return;
  }
  
  const newChatId = '';
  currentChatId.value = newChatId;
  chatIdStore.chatId = newChatId;  // 将新对话ID存储到pinia中
  currentMessages.value = [];
  
  // 添加一条欢迎消息
  currentMessages.value = [{
    role: 'assistant',
    content: '🌌 您好！我是MuseLink-千鉴，很荣幸以这个融合科技与文明深度的身份与您相遇。专注于使用数据链解码青铜铭文与千手观音的时空密语，此刻正从王莽"一刀五千"刀币护身符的祥云纹中，为您打捞文明星尘✨',
    timestamp: new Date()
  }];
  
  // 显示常见问题按钮
  showQuickQuestions.value = true;
}


onMounted(async () => {
  // 先获取用户信息
  await fetchUserInfo()
  
  // 再加载聊天历史记录
  await loadChatHistory()
  
  // 检查是否有存储的chatId
  if (chatIdStore.chatId) {
    // 如果有存储的chatId，尝试加载该对话
    try {
      await loadChat(chatIdStore.chatId)
      console.log('已恢复上次对话:', chatIdStore.chatId)
    } catch (error) {
      console.error('恢复上次对话失败:', error)
      // 如果加载失败，重置并创建新对话
      chatIdStore.chatId = ''
      startNewChat()
    }
  } else {
    // 如果没有存储的chatId，创建新对话
    startNewChat()
  }
  
  // 调整输入框高度
  adjustTextareaHeight()
})

const handleSessionCommand = async (chatId, command) => {
  if (command === 'rename') {
    try {
      const { value } = await ElMessageBox.prompt('请输入新的对话名称', '重命名', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '对话名称不能为空'
      })
      
      // 调用API进行重命名
      await chatAPI.renameChat(chatId, value);
      
      // 更新前端显示
      const chat = chatHistory.value.find(item => item.id === chatId)
      if (chat) {
        chat.title = value
        ElMessage.success('重命名成功')
      }
    } catch (error) {
      if (error === 'cancel') {
        // 用户取消操作，不做处理
      } else {
        // API调用失败
        console.error('重命名失败:', error);
        ElMessage.error('重命名失败，请稍后重试');
      }
    }
  } else if (command === 'delete') {
      try {
        await ElMessageBox.confirm('确定要删除这个对话吗？', '删除确认', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 调用API删除对话
        await chatAPI.deleteChat(chatId);
        
        // 在API调用成功后更新前端显示
        chatHistory.value = chatHistory.value.filter(item => item.id !== chatId)
        
        // 如果删除的是当前对话，则开始一个新对话
        if (currentChatId.value === chatId) {
          startNewChat()
        }
        
        ElMessage.success('删除成功')
      } catch (error) {
        if (error === 'cancel') {
          // 用户取消删除，不做处理
        } else {
          // API调用失败
          console.error('删除对话失败:', error);
          ElMessage.error('删除失败，请稍后重试');
        }
      }
    }
}

// 添加常见问题数组
const commonQuestions = [
  "数据库中有哪些博物馆呢？",
  "给我推荐一些宾夕法尼亚博物馆的文物？",
  "六弦琵琶的年代是什么？",
  "风吹牡丹是否为瓷器？",
  "请介绍一下带盖糖碗的特点",
  "蝴蝶吊坠的收藏地在哪里？",
  "孔雀蓝釉花瓶的作者是谁？"
]

// 控制是否显示快速问题按钮
const showQuickQuestions = ref(false)

// 处理快速问题点击
const handleQuickQuestion = (question) => {
  userInput.value = question
  sendMessage()
  showQuickQuestions.value = false // 问题发送后隐藏按钮区域
}

</script>

<style scoped lang="scss">
.ai-chat {
  position: fixed;
  top: 112px; // 修改固定值为112px以适应NavBar的总高度（顶部栏+主导航栏）
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  background: #f7f9fc; // 使用固定的浅色背景
  overflow: hidden;

  .chat-container {
    flex: 1;
    display: flex;
    max-width: 1800px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem 2rem;
    gap: 1.5rem;
    height: 100%;
    overflow: hidden;
  }

  .sidebar {
    width: 300px;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    
    .history-header {
      flex-shrink: 0;
      padding: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 {
        font-size: 1.25rem;
      }
      
      .new-chat {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background: #007CF0;
        color: white;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background: #0066cc;
        }
        
        .icon {
          width: 1.25rem;
          height: 1.25rem;
        }
      }
    }
    
    .history-list {
      flex: 1;
      overflow-y: auto;
      padding: 0 1rem 1rem;
      
      .history-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background: rgba(0, 0, 0, 0.05);
        }
        
        &.active {
          background: rgba(0, 124, 240, 0.1);
        }
        
        .icon {
          width: 1.25rem;
          height: 1.25rem;
        }
        
        .title {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 2rem;
    }
    
    .input-area {
      flex-shrink: 0;
      padding: 1.5rem 2rem;
      background: rgba(255, 255, 255, 0.98);
      border-top: 1px solid rgba(0, 0, 0, 0.05);
      display: flex;
      flex-direction: column;
      gap: 1rem;

      .input-row {
        display: flex;
        gap: 1rem;
        align-items: center;
        background: #fff;
        padding: 0.75rem;
        border-radius: 1rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

        .rag-button {
          flex-shrink: 0;
          min-width: 60px;
          height: 32px;
          margin-right: 4px;
        }
          
        textarea {
          flex: 1;
          resize: none;
          border: none;
          background: transparent;
          padding: 0.75rem;
          color: inherit;
          font-family: inherit;
          font-size: 1rem;
          line-height: 1.5;
          max-height: 150px;
          
          &:focus {
            outline: none;
          }
          
          &::placeholder {
            color: #999;
          }
        }
        
        .send-button {
          width: 2.5rem;
          height: 2.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 0.75rem;
          background: #007CF0;
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover:not(:disabled) {
            background: #0066cc;
            transform: translateY(-1px);
          }
          
          &:disabled {
            background: #ccc;
            cursor: not-allowed;
          }
          
          .icon {
            width: 1.25rem;
            height: 1.25rem;
          }
        }
      }
    }
  }
}

// 删除所有.dark相关的样式

// 添加常见问题样式
.quick-questions {
  margin-top: 1.5rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background-color: rgba(0, 0, 0, 0.03);
  
  h3 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #666;
  }
  
  .questions-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    
    .question-btn {
      padding: 0.5rem 1rem;
      border-radius: 1rem;
      background-color: #f0f0f0;
      border: 1px solid #ddd;
      cursor: pointer;
      transition: all 0.2s;
      font-size: 0.9rem;
      
      &:hover {
        background-color: #e0e0e0;
        transform: translateY(-1px);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
  }
}

// 基础下拉菜单样式
:deep(.el-dropdown-menu) {
  border-radius: 0.5rem;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.history-item {
  :deep(.el-button) {
    color: #606266;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
  }
}

@media (max-width: 768px) {
  .ai-chat {
    top: 130px; // 在移动视图下增加顶部间距，因为NavBar在小屏幕上可能会变高
    .chat-container {
      padding: 0;
    }
    
    .sidebar {
      display: none; // 在移动端隐藏侧边栏
    }
    
    .chat-main {
      border-radius: 0;
    }
  }
}

@media (max-width: 480px) {
  .ai-chat {
    top: 145px; // 在更小的屏幕上进一步调整
  }
}

/* 通用样式 */
.el-dropdown__popper.el-popper,
.el-popper.is-light {
  border-radius: 0.5rem !important;
}

/* RAG提示框样式 */
.rag-tooltip {
  max-width: 300px !important;
  font-size: 0.85rem !important;
  line-height: 1.5 !important;
  padding: 8px 12px !important;
}
</style>

<style lang="scss">
/* 确保弹出层的圆角一致 */
.el-dropdown-menu {
  border-radius: 8px !important;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3) !important;
}
</style>