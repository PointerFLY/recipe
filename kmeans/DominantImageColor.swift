//
//  DominantImageColor.swift
//
//  Created by PointerFLY on 22/8/19.
//  Copyright © 2019 PointerFLY. All rights reserved.
//

import UIKit

extension DominantImageColor {
    struct Vector {
        let x: CGFloat
        let y: CGFloat
        let z: CGFloat
    
        static let kScale: CGFloat = 100.0
    
        init(x: CGFloat, y: CGFloat, z: CGFloat) {
            self.x = x
            self.y = y
            self.z = z
        }
    
        init(hue: CGFloat, saturation: CGFloat, brightness: CGFloat) {
            x = hue * Vector.kScale
            y = saturation * Vector.kScale
            z = brightness * Vector.kScale
        }
    
        func uiColor() -> UIColor {
            return UIColor(hue: x / Vector.kScale, saturation: y / Vector.kScale, brightness: z / Vector.kScale, alpha: 1.0)
        }
    
        static func distanceOf(v1: Vector, v2: Vector) -> CGFloat {
            return sqrt(pow(v1.x - v2.x, 2) + pow(v1.y - v2.y, 2) + pow(v1.z - v2.z, 2))
        }
    }
}

class DominantImageColor {
    
    struct Const {
        static let classCount = 5
        static let maxImageHeight: CGFloat = 50.0
        static let convergentDistance: CGFloat = 3.0
        static let maxIterationCount: Int = 15
        static let intensityThreshold: CGFloat = 0.3
        static let stride = 4
    }

    static func colorFromImage(_ image: UIImage) -> UIColor? {
        guard let bytes = bytesFromImage(image) else { return nil }
        
        let vectors = vectorsFromBytes(bytes: bytes)
        let result = kmeans(vectors: vectors, k: Const.classCount)
        
        return result.uiColor()
    }

    static func kmeans(vectors: [Vector], k: Int) -> Vector {
        var centroids = [Vector]()
        let subcount = vectors.count / k
        for i in 0..<k {
            centroids.append(vectors[subcount / 2 + subcount * i])
        }
        
        // Use index in vectors to identify a vector
        var clusters: [[Int]]
        var centerMoveDistance = CGFloat.greatestFiniteMagnitude
        var iterationCount = 0
        
        repeat {
            // Find closest cluster center for every vector
            clusters = [[Int]](repeating: [Int](), count: k)
            for i in 0..<vectors.count {
                let vector = vectors[i]
                
                var closestIndex = 0
                var closestDistance: CGFloat = CGFloat.greatestFiniteMagnitude
                for j in 0..<centroids.count {
                    let center = centroids[j]
                    let distance = Vector.distanceOf(v1: center, v2: vector)
                    if distance < closestDistance {
                        closestDistance = distance
                        closestIndex = j
                    }
                }
                
                clusters[closestIndex].append(i)
            }
            
            // Create new center
            centerMoveDistance = 0
            for i in 0..<clusters.count {
                let vectorIndices = clusters[i]
                
                var xSum: CGFloat = 0.0
                var ySum: CGFloat = 0.0
                var zSum: CGFloat = 0.0
                for idx in vectorIndices {
                    let vector = vectors[idx]
                    xSum += vector.x
                    ySum += vector.y
                    zSum += vector.z
                }
                
                let xMean = xSum.isZero ? xSum : xSum / CGFloat(vectorIndices.count)
                let yMean = ySum.isZero ? ySum : ySum / CGFloat(vectorIndices.count)
                let zMean = zSum.isZero ? zSum : zSum / CGFloat(vectorIndices.count)
                let newCenter = Vector(x: xMean, y: yMean, z: zMean)
                centerMoveDistance += Vector.distanceOf(v1: newCenter, v2: centroids[i])
                
                centroids[i] = newCenter
            }
            
            iterationCount += 1
        } while centerMoveDistance > Const.convergentDistance && iterationCount < Const.maxIterationCount
        
        // Find cluster with best score
        var bestScore: CGFloat = 0
        var bestIndex = 0
        for i in 0..<clusters.count {
            var score: CGFloat = 0
            var intensity: CGFloat = 0
            centroids[i].uiColor().getWhite(&intensity, alpha: nil)
            
            score = intensity > Const.intensityThreshold ? 1 - intensity : CGFloat(clusters[i].count)
            if score > bestScore {
                bestScore = score
                bestIndex = i
            }
        }
        return centroids[bestIndex]
    }
    
    static func vectorsFromBytes(bytes: [UInt8]) -> [Vector] {
        var vectors = [Vector]()
        for i in stride(from: 0, to: bytes.count / Const.stride, by: 4) {
            let blue = CGFloat(bytes[i * Const.stride + 1]) / 255.0
            let green = CGFloat(bytes[i * Const.stride + 2]) / 255.0
            let red = CGFloat(bytes[i * Const.stride + 3]) / 255.0
            let color = UIColor(red: red, green: green, blue: blue, alpha: 1.0)
            
            var h: CGFloat = 0
            var s: CGFloat = 0
            var b: CGFloat = 0
            color.getHue(&h, saturation: &s, brightness: &b, alpha: nil)
            
            let vector = Vector(hue: h, saturation: s, brightness: b)
            vectors.append(vector)
        }
        
        return vectors
    }

    static func bytesFromImage(_ image: UIImage) -> [UInt8]? {
        var resizedImage: UIImage?
        if image.size.height > Const.maxImageHeight {
            let ratio = Const.maxImageHeight / image.size.height
            let newWidth = image.size.width * ratio
            let newHeight = image.size.height * ratio
            
            UIGraphicsBeginImageContext(CGSize(width: newWidth, height: newHeight))
            image.draw(in: CGRect(x: 0, y: 0, width: newWidth, height: newHeight))
            resizedImage = UIGraphicsGetImageFromCurrentImageContext()
            UIGraphicsEndImageContext()
        }
        
        guard let image = resizedImage?.cgImage else { return nil }
        
        let width = image.width
        let height = image.height
        
        var rawData = [UInt8](repeating: 0, count: width * height * 4)
        guard let context = CGContext(
            data: &rawData,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: 4 * width,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) else {
                return nil
        }
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        
        return rawData
    }
}
