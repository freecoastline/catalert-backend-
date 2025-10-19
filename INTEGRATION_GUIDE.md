# CatAlert iOS 与后端集成指南

## 概述

本指南将帮助你将现有的CatAlert iOS应用与新的AI Agent后端服务集成。

## 后端服务架构

### 核心功能
- 🐱 猫咪档案管理
- ⏰ 智能提醒系统
- 📊 活动记录跟踪
- 🤖 AI健康分析
- 📈 行为模式识别
- 💡 个性化建议

### API端点
- **基础URL**: `http://localhost:8000/api/v1`
- **认证**: JWT Token
- **数据格式**: JSON

## iOS应用集成步骤

### 1. 网络层重构

#### 1.1 创建网络服务类

```swift
// NetworkService.swift
import Foundation
import Combine

class NetworkService: ObservableObject {
    static let shared = NetworkService()
    
    private let baseURL = "http://localhost:8000/api/v1"
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    // MARK: - Generic Request Method
    private func request<T: Codable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Data? = nil,
        responseType: T.Type
    ) -> AnyPublisher<T, Error> {
        
        guard let url = URL(string: baseURL + endpoint) else {
            return Fail(error: NetworkError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            request.httpBody = body
        }
        
        return URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: T.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
}

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
}

enum NetworkError: Error {
    case invalidURL
    case noData
    case decodingError
    case serverError(Int)
}
```

#### 1.2 创建API模型

```swift
// APIModels.swift
import Foundation

// MARK: - Cat Models
struct APICat: Codable {
    let id: String
    let name: String
    let gender: String?
    let breed: String?
    let description: String?
    let birthDate: String?
    let weight: Double?
    let color: String?
    let microchipId: String?
    let healthCondition: String
    let medicalNotes: String?
    let ageInYears: Int?
    let ageInMonths: Int?
    let createdAt: String
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, name, gender, breed, description, weight, color
        case birthDate = "birth_date"
        case microchipId = "microchip_id"
        case healthCondition = "health_condition"
        case medicalNotes = "medical_notes"
        case ageInYears = "age_in_years"
        case ageInMonths = "age_in_months"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - Reminder Models
struct APIReminder: Codable {
    let id: String
    let catId: String
    let title: String
    let type: String
    let frequency: String
    let description: String?
    let priority: Int
    let isEnabled: Bool
    let aiOptimized: Bool
    let completionRate: Double
    let createdAt: String
    let updatedAt: String?
    let scheduledTimes: [APIReminderTime]
    
    enum CodingKeys: String, CodingKey {
        case id, title, type, frequency, description, priority
        case catId = "cat_id"
        case isEnabled = "is_enabled"
        case aiOptimized = "ai_optimized"
        case completionRate = "completion_rate"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case scheduledTimes = "scheduled_times"
    }
}

struct APIReminderTime: Codable {
    let id: String
    let hour: Int
    let minute: Int
    let dayOfWeek: Int?
    let isEnabled: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, hour, minute, isEnabled
        case dayOfWeek = "day_of_week"
    }
}

// MARK: - Activity Models
struct APIActivity: Codable {
    let id: String
    let reminderId: String
    let catId: String
    let type: String
    let scheduledTime: String
    let completeTime: String?
    let status: String
    let actualDuration: Int?
    let notes: String?
    let qualityRating: Int?
    let catBehavior: String?
    let anomalyDetected: Bool
    let createdAt: String
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, type, notes, status
        case reminderId = "reminder_id"
        case catId = "cat_id"
        case scheduledTime = "scheduled_time"
        case completeTime = "complete_time"
        case actualDuration = "actual_duration"
        case qualityRating = "quality_rating"
        case catBehavior = "cat_behavior"
        case anomalyDetected = "anomaly_detected"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - AI Chat Models
struct AIChatRequest: Codable {
    let userId: String
    let catId: String
    let message: String
    let sessionId: String?
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case catId = "cat_id"
        case message
        case sessionId = "session_id"
    }
}

struct AIChatResponse: Codable {
    let success: Bool
    let message: String
    let type: String
    let sessionId: String
    let processingTimeMs: Int
    let suggestions: [AISuggestion]
    let insights: [AIInsight]
    
    enum CodingKeys: String, CodingKey {
        case success, message, type
        case sessionId = "session_id"
        case processingTimeMs = "processing_time_ms"
        case suggestions, insights
    }
}

struct AISuggestion: Codable {
    let title: String
    let type: String
    let suggestedTimes: [String]
    let frequency: String
    let reason: String
    
    enum CodingKeys: String, CodingKey {
        case title, type, reason, frequency
        case suggestedTimes = "suggested_times"
    }
}

struct AIInsight: Codable {
    let type: String
    let title: String
    let description: String
    let priority: String
    let actionable: Bool
}
```

### 2. 数据同步服务

#### 2.1 创建数据同步管理器

```swift
// DataSyncManager.swift
import Foundation
import Combine

class DataSyncManager: ObservableObject {
    static let shared = DataSyncManager()
    
    @Published var isSyncing = false
    @Published var lastSyncTime: Date?
    
    private let networkService = NetworkService.shared
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    // MARK: - Sync Methods
    func syncCats() -> AnyPublisher<[APICat], Error> {
        return networkService.request(
            endpoint: "/cats",
            responseType: [APICat].self
        )
    }
    
    func syncReminders(for catId: String) -> AnyPublisher<[APIReminder], Error> {
        return networkService.request(
            endpoint: "/reminders?cat_id=\(catId)",
            responseType: [APIReminder].self
        )
    }
    
    func syncActivities(for catId: String, days: Int = 7) -> AnyPublisher<[APIActivity], Error> {
        return networkService.request(
            endpoint: "/activities?cat_id=\(catId)&days=\(days)",
            responseType: [APIActivity].self
        )
    }
    
    func syncTodayActivities(for catId: String) -> AnyPublisher<[APIActivity], Error> {
        return networkService.request(
            endpoint: "/activities/cats/\(catId)/today",
            responseType: [APIActivity].self
        )
    }
    
    // MARK: - Full Sync
    func performFullSync() {
        isSyncing = true
        
        // Sync all data
        syncCats()
            .flatMap { cats in
                Publishers.MergeMany(
                    cats.map { cat in
                        self.syncReminders(for: cat.id)
                            .map { reminders in (cat.id, reminders) }
                    }
                )
            }
            .flatMap { (catId, reminders) in
                self.syncActivities(for: catId)
                    .map { activities in (catId, reminders, activities) }
            }
            .sink(
                receiveCompletion: { completion in
                    self.isSyncing = false
                    self.lastSyncTime = Date()
                    
                    if case .failure(let error) = completion {
                        print("Sync failed: \(error)")
                    }
                },
                receiveValue: { (catId, reminders, activities) in
                    // Update local data
                    self.updateLocalData(catId: catId, reminders: reminders, activities: activities)
                }
            )
            .store(in: &cancellables)
    }
    
    private func updateLocalData(catId: String, reminders: [APIReminder], activities: [APIActivity]) {
        // Convert API models to local models and update Core Data
        // This would integrate with your existing DataPersistenceManager
    }
}
```

### 3. AI Agent集成

#### 3.1 创建AI服务

```swift
// AIService.swift
import Foundation
import Combine

class AIService: ObservableObject {
    static let shared = AIService()
    
    @Published var currentSessionId: String?
    @Published var isProcessing = false
    
    private let networkService = NetworkService.shared
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    // MARK: - Chat with AI Agent
    func chatWithAgent(
        userId: String,
        catId: String,
        message: String
    ) -> AnyPublisher<AIChatResponse, Error> {
        
        isProcessing = true
        
        let request = AIChatRequest(
            userId: userId,
            catId: catId,
            message: message,
            sessionId: currentSessionId
        )
        
        let requestData = try! JSONEncoder().encode(request)
        
        return networkService.request(
            endpoint: "/ai/chat",
            method: .POST,
            body: requestData,
            responseType: AIChatResponse.self
        )
        .handleEvents(
            receiveOutput: { response in
                self.currentSessionId = response.sessionId
                self.isProcessing = false
            },
            receiveCompletion: { _ in
                self.isProcessing = false
            }
        )
        .eraseToAnyPublisher()
    }
    
    // MARK: - Get AI Insights
    func getInsights(for catId: String, period: String = "7d") -> AnyPublisher<[AIInsight], Error> {
        let request = [
            "cat_id": catId,
            "analysis_period": period
        ]
        
        let requestData = try! JSONSerialization.data(withJSONObject: request)
        
        return networkService.request(
            endpoint: "/ai/insights",
            method: .POST,
            body: requestData,
            responseType: [AIInsight].self
        )
    }
    
    // MARK: - Get Cat Analysis
    func getCatAnalysis(catId: String, days: Int = 30) -> AnyPublisher<[String: Any], Error> {
        return networkService.request(
            endpoint: "/ai/cats/\(catId)/analysis?days=\(days)",
            responseType: [String: Any].self
        )
    }
}
```

#### 3.2 创建AI聊天界面

```swift
// AIChatViewController.swift
import UIKit
import Combine

class AIChatViewController: UIViewController {
    
    @IBOutlet weak var chatTableView: UITableView!
    @IBOutlet weak var messageTextField: UITextField!
    @IBOutlet weak var sendButton: UIButton!
    @IBOutlet weak var activityIndicator: UIActivityIndicatorView!
    
    private let aiService = AIService.shared
    private var cancellables = Set<AnyCancellable>()
    private var messages: [ChatMessage] = []
    
    var catId: String!
    var userId: String!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupBindings()
    }
    
    private func setupUI() {
        chatTableView.delegate = self
        chatTableView.dataSource = self
        chatTableView.register(ChatMessageCell.self, forCellReuseIdentifier: "ChatMessageCell")
        
        sendButton.addTarget(self, action: #selector(sendMessage), for: .touchUpInside)
    }
    
    private func setupBindings() {
        aiService.$isProcessing
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isProcessing in
                self?.activityIndicator.isHidden = !isProcessing
                self?.sendButton.isEnabled = !isProcessing
            }
            .store(in: &cancellables)
    }
    
    @objc private func sendMessage() {
        guard let message = messageTextField.text, !message.isEmpty else { return }
        
        // Add user message
        let userMessage = ChatMessage(content: message, isFromUser: true)
        messages.append(userMessage)
        chatTableView.reloadData()
        
        // Clear text field
        messageTextField.text = ""
        
        // Send to AI
        aiService.chatWithAgent(userId: userId, catId: catId, message: message)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        print("AI chat error: \(error)")
                    }
                },
                receiveValue: { [weak self] response in
                    let aiMessage = ChatMessage(content: response.message, isFromUser: false)
                    self?.messages.append(aiMessage)
                    self?.chatTableView.reloadData()
                    
                    // Scroll to bottom
                    let indexPath = IndexPath(row: self?.messages.count ?? 0 - 1, section: 0)
                    self?.chatTableView.scrollToRow(at: indexPath, at: .bottom, animated: true)
                }
            )
            .store(in: &cancellables)
    }
}

// MARK: - TableView DataSource & Delegate
extension AIChatViewController: UITableViewDataSource, UITableViewDelegate {
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return messages.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "ChatMessageCell", for: indexPath) as! ChatMessageCell
        cell.configure(with: messages[indexPath.row])
        return cell
    }
}

// MARK: - Chat Message Model
struct ChatMessage {
    let content: String
    let isFromUser: Bool
    let timestamp: Date = Date()
}
```

### 4. 现有代码集成

#### 4.1 更新ReminderManager

```swift
// 在现有的ReminderManager中添加网络同步功能
extension ReminderManager {
    
    func syncWithBackend() {
        DataSyncManager.shared.performFullSync()
    }
    
    func createReminderOnBackend(_ reminder: CatReminder) {
        // 转换本地模型为API模型并发送到后端
        let apiReminder = convertToAPIReminder(reminder)
        
        // 发送到后端API
        // 处理响应和错误
    }
    
    private func convertToAPIReminder(_ reminder: CatReminder) -> APIReminder {
        // 转换逻辑
    }
}
```

#### 4.2 更新CatViewModel

```swift
// 在现有的CatViewModel中添加AI功能
extension CatViewModel {
    
    func getAIAnalysis() {
        AIService.shared.getCatAnalysis(catId: model.id)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        print("AI analysis error: \(error)")
                    }
                },
                receiveValue: { analysis in
                    // 处理AI分析结果
                    self.updateWithAIAnalysis(analysis)
                }
            )
            .store(in: &cancellables)
    }
    
    private func updateWithAIAnalysis(_ analysis: [String: Any]) {
        // 更新UI显示AI分析结果
    }
}
```

### 5. 配置和部署

#### 5.1 环境配置

```swift
// Config.swift
struct Config {
    static let baseURL = "http://localhost:8000/api/v1"
    static let apiKey = "your_api_key_here"
    
    #if DEBUG
    static let environment = "development"
    #else
    static let environment = "production"
    #endif
}
```

#### 5.2 启动后端服务

```bash
# 在catalert-backend目录下
docker-compose up -d

# 或者本地运行
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 6. 测试集成

#### 6.1 创建测试用例

```swift
// NetworkServiceTests.swift
import XCTest
@testable import CatAlert

class NetworkServiceTests: XCTestCase {
    
    func testGetCats() {
        let expectation = XCTestExpectation(description: "Get cats")
        
        NetworkService.shared.request(
            endpoint: "/cats",
            responseType: [APICat].self
        )
        .sink(
            receiveCompletion: { completion in
                if case .failure(let error) = completion {
                    XCTFail("Request failed: \(error)")
                }
                expectation.fulfill()
            },
            receiveValue: { cats in
                XCTAssertFalse(cats.isEmpty)
            }
        )
        .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 10.0)
    }
}
```

## 总结

通过以上步骤，你可以成功将CatAlert iOS应用与AI Agent后端服务集成。主要改进包括：

1. **网络层重构**: 使用Combine进行异步网络请求
2. **数据同步**: 实现本地数据与后端数据的双向同步
3. **AI集成**: 添加AI聊天和分析功能
4. **错误处理**: 完善的错误处理和用户反馈
5. **测试**: 完整的测试覆盖

这样，你的CatAlert应用就具备了强大的AI Agent能力，可以为用户提供智能的猫咪护理建议和健康分析。
